#!/usr/bin/env python3

#neccessary libraries needed to run script
import yaml
import sys
import time
import requests
from typing import List, Dict
from urllib.parse import urlparse
from collections import defaultdict

# takes the yaml file, and returns the contents as a list of dicts
def load_endpoints(file_path: str) -> List[Dict]:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# makes sure each endpoint has a name and url field. then processes each endpoint
def validate_endpoint(endpoint: Dict) -> bool:
    required_fields = ['name', 'url']
    return all(field in endpoint for field in required_fields)

def parse_endpoint(endpoint: Dict) -> Dict:
    parsed = {
        'name': endpoint['name'],
        'url': endpoint['url'],
        'method': endpoint.get('method', 'GET'),
        'headers': endpoint.get('headers', {}),
        'body': endpoint.get('body'),
        'domain': urlparse(endpoint['url']).netloc,
        'checks': [],
    }
    
    parsed['parsed_url'] = urlparse(parsed['url'])
    if not all([parsed['parsed_url'].scheme, parsed['parsed_url'].netloc]):
        raise ValueError(f"Invalid URL: {parsed['url']}")
    
    return parsed

# health check funct, sends http request to get status codes
def check_endpoint_health(endpoint: Dict) -> bool:
    try:
        start_time = time.time()
        response = requests.request(
            method=endpoint['method'],
            url=endpoint['url'],
            headers=endpoint['headers'],
            data=endpoint.get('body'),
            timeout=10
        )
        response_time = (time.time() - start_time) * 1000  

        is_up = 200 <= response.status_code < 300 and response_time < 500
        return is_up
    except requests.RequestException:
        return False

# calculates the % for each domain
def calculate_availability(endpoints: List[Dict]) -> Dict[str, float]:
    domain_checks = defaultdict(lambda: {'up': 0, 'total': 0})
    
    for endpoint in endpoints:
        domain = endpoint['domain']
        up_count = sum(endpoint['checks'])
        total_count = len(endpoint['checks'])
        
        domain_checks[domain]['up'] += up_count
        domain_checks[domain]['total'] += total_count
    
    availability = {}
    for domain, checks in domain_checks.items():
        if checks['total'] > 0:
            availability[domain] = round(100 * checks['up'] / checks['total'])
        else:
            availability[domain] = 0
    
    return availability

# logging, printing the %
def log_availability(availability: Dict[str, float]):
    for domain, percentage in availability.items():
        print(f"{domain} has {percentage}% availability percentage")
    print()  

# this is the loop, 15sec delay, checking each endpoint
def run_health_checks(endpoints: List[Dict]):
    try:
        while True:
            for endpoint in endpoints:
                is_up = check_endpoint_health(endpoint)
                endpoint['checks'].append(is_up)
                status = "UP" if is_up else "DOWN"
                print(f"{endpoint['name']}: {status}")
            
            availability = calculate_availability(endpoints)
            log_availability(availability)
            
            print("--- Waiting 15 seconds for next check ---\n")
            time.sleep(15)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

# main function.
def main():
    if len(sys.argv) < 2:
        print("Please provide the path to the YAML input file.")
        sys.exit(1)

    input_file = sys.argv[1]
    endpoints = load_endpoints(input_file)

    parsed_endpoints = []
    for endpoint in endpoints:
        if validate_endpoint(endpoint):
            try:
                parsed_endpoints.append(parse_endpoint(endpoint))
            except ValueError as e:
                print(f"Error parsing endpoint {endpoint['name']}: {str(e)}")
        else:
            print(f"Skipping invalid endpoint: {endpoint}")

    print(f"Loaded {len(parsed_endpoints)} valid endpoints")
    for endpoint in parsed_endpoints:
        print(f"- {endpoint['name']}: {endpoint['url']} ({endpoint['method']})")

    print("\nStarting health checks...")
    run_health_checks(parsed_endpoints)

if __name__ == "__main__":
    main()

# In company setting would see which functions are reusuable and create an internal library
# of functions. Doing that would clean up the code by importing those libraries
# so we dont have to write out logic.
# & Parameterize functions!