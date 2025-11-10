#!/bin/bash

# Test runner script for the FastAPI application

echo "Running FastAPI tests with coverage..."
echo "======================================="

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "Test run completed!"
echo "Coverage report saved to htmlcov/index.html"