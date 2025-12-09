# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import time
import math
import requests
from concurrent import futures

CALLBACK_URL = "http://localhost:80/calc/"

SPEED_OF_LIGHT = 3.0e8

executor = futures.ThreadPoolExecutor(max_workers=1)

def en_and_ni_calculation(inp_dist, inp_texp, inp_mass, scope_lambda, scope_delta_lamb, scope_zero_point):
    E_SN = (4 * math.pi * math.pow(inp_dist, 2) * inp_texp * 
            scope_lambda * scope_delta_lamb) / (SPEED_OF_LIGHT * scope_zero_point) * math.pow(10, (-0.4 * inp_mass))
    
    M_Ni56 = 1.2e-7 * (math.pow(inp_dist, 2) / scope_delta_lamb) * math.pow(10, -0.4 * inp_mass) * math.pow(scope_lambda / 500.0, 2)
    
    return float(E_SN), float(M_Ni56)

def process_calculation(request_data):
    
    delay_seconds = 5 + (hash(str(request_data.get("calc_id"))) % 6)  
    time.sleep(delay_seconds)
    
    inp_dist = float(request_data.get("inp_dist"))
    inp_texp = float(request_data.get("inp_texp"))
    inp_mass = float(request_data.get("inp_mass"))
    scope_lambda = float(request_data.get("scope_lambda"))
    scope_delta_lamb = float(request_data.get("scope_delta_lamb"))
    scope_zero_point = float(request_data.get("scope_zero_point"))
    calc_id = request_data.get("calc_id")
    star_id = request_data.get("star_id")
    
    E_SN, M_Ni56 = en_and_ni_calculation(
        inp_dist, inp_texp, inp_mass,
        scope_lambda, scope_delta_lamb, scope_zero_point
    )
    
    return {
        "calc_id": calc_id,
        "star_id": star_id,
        "res_en": E_SN,
        "res_ni": M_Ni56
    }
    
def calculation_callback(task):
    try:
        result = task.result()
        print(f"Calculation completed: {result}")
        
    except Exception as e:
        print(f"Calculation failed: {e}")
        return
    
    calc_id = result.get("calc_id")
    
    if '_' in calc_id:
        parts = calc_id.split('_')
        star_id = parts[0] 
        scope_id = parts[1]
    else:
        star_id = result.get("star_id")
        scope_id = result.get("scope_id") 
        
    callback_data = {
        "star_id": star_id,
        "scope_id": scope_id,
        "res_en": result.get("res_en"),
        "res_ni": result.get("res_ni")
    }
    
    print(f"Sending callback: {callback_data}")
    
    
    AUTH_TOKEN = "secret123"
    headers = {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(
            CALLBACK_URL,
            json=callback_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Results sent successfully to main service")
        else:
            print(f"Failed to send results: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending callback: {e}")

@api_view(['POST'])
def calculate(request):

    required_fields = ["calc_id", "star_id", "inp_dist", "inp_texp", "inp_mass", 
                      "scope_lambda", "scope_delta_lamb", "scope_zero_point"]
    
    for field in required_fields:
        if field not in request.data:
            return Response(
                {"error": f"Missing required field: {field}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        task = executor.submit(process_calculation, request.data)
        task.add_done_callback(calculation_callback)
        
        return Response({
            "message": "Calculation started",
            "calc_id": request.data.get("calc_id"),
            "star_id": request.data.get("star_id"),
            "delay": "5-10 seconds"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to start calculation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "service": "async-calculation-service"
    }, status=status.HTTP_200_OK)