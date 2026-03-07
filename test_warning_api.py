#!/usr/bin/env python3
"""Test script to verify real_transaction_warning field in API response"""
import requests
import json

def test_warning_field():
    url = "http://localhost:8000/auction"
    params = {"case_no": "2024타경579705"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        result_data = data.get('data', {})

        print("=" * 60)
        print("API Response Test - real_transaction_warning Field")
        print("=" * 60)
        print(f"Success: {data.get('success')}")
        print(f"\nTransaction Count: {result_data.get('transactions_count')}")
        print(f"Real Transaction Note: {result_data.get('real_transaction_note')}")
        print(f"\nReal Transaction Warning:")
        print(f"  {result_data.get('real_transaction_warning', 'NOT FOUND')}")
        print("\n" + "=" * 60)

        if 'real_transaction_warning' in result_data:
            print("✓ Field 'real_transaction_warning' exists in response!")
        else:
            print("✗ Field 'real_transaction_warning' NOT found in response!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_warning_field()
