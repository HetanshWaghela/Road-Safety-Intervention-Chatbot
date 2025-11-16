# Usage Guide - Logging, Frontend, and Testing Improvements

This guide explains how to use the newly implemented improvements for logging, frontend enhancements, and testing.

## Table of Contents
1. [Setup](#setup)
2. [Using Structured Logging](#using-structured-logging)
3. [Using the Enhanced Frontend](#using-the-enhanced-frontend)
4. [Running Tests](#running-tests)
5. [Understanding Evaluation Metrics](#understanding-evaluation-metrics)

---

## Setup

### 1. Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `python-json-logger==2.0.7` for structured logging.

### 2. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The backend will now use structured JSON logging automatically. Logs will be in JSON format in the console.

### 3. Start the Frontend

```bash
cd frontend
streamlit run app.py
```

---

## Using Structured Logging

### What Changed

- **All logs are now in JSON format** - Easy to parse and analyze
- **Request IDs** - Every request gets a unique ID for tracking
- **Evaluation metrics** - Every search query logs relevance and comprehensiveness scores

### Viewing Logs

Logs are output to the console in JSON format. Example:

```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "levelname": "INFO",
  "name": "app.core.orchestrator",
  "message": "Search query evaluation metrics",
  "request_id": "abc123-def456-ghi789",
  "query": "Faded STOP sign on 65 kmph highway",
  "relevance_score": 0.85,
  "comprehensiveness_score": 0.78,
  "confidence_scores": [0.95, 0.87, 0.82],
  "top_confidence": 0.95,
  "avg_confidence": 0.88,
  "response_time_ms": 342
}
```

### Logging Evaluation Metrics

The system automatically logs evaluation metrics for every search query:

- **relevance_score**: How well results match the query (0-1)
- **comprehensiveness_score**: How detailed and complete the results are (0-1)
- **confidence_scores**: Array of confidence scores for each result
- **top_confidence**: Highest confidence score
- **avg_confidence**: Average confidence across all results

### Request Tracking

Every API request gets a unique `request_id` that appears in all related logs. This helps track a request through the entire system.

Look for the `X-Request-ID` header in API responses to correlate with logs.

---

## Using the Enhanced Frontend

### New Features

1. **Better Results Display**
   - Top recommendation is prominently displayed with "BEST MATCH" badge
   - Clear "Why This Intervention?" section with explanations
   - IRC database references highlighted with badges

2. **Error Handling**
   - User-friendly error messages (not technical stack traces)
   - Categorized errors: Network, API, Validation
   - Retry buttons for failed requests
   - Helpful suggestions when errors occur

3. **Loading States**
   - Progress indicators during search
   - Status messages showing what's happening

4. **Export Functionality**
   - Download results as JSON
   - Copy results to clipboard

### Using the Frontend

1. **Start the frontend**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

2. **Open in browser**: http://localhost:8501

3. **Search for interventions**:
   - Enter a query like "Faded STOP sign on 65 kmph highway"
   - Click "🔍 Search"
   - View the enhanced results with:
     - Top recommendation clearly marked
     - Explanation section showing why it matches
     - IRC database references
     - Detailed specifications

4. **Handle Errors**:
   - If an error occurs, you'll see a user-friendly message
   - Click "🔄 Retry" to try again
   - Check the suggestions provided

5. **Export Results**:
   - After a successful search, use "📥 Download Results (JSON)" to save
   - Or use "📋 Copy to Clipboard" to copy results

### Example Queries to Try

- "Faded STOP sign on 65 kmph highway"
- "Missing road markings at pedestrian crossing"
- "Damaged speed breaker on urban road"
- "Obstruction blocking road sign visibility"

---

## Running Tests

### 1. Run Evaluation Test Suite

```bash
cd backend
python scripts/test_queries.py
```

This will:
- Test multiple queries
- Evaluate relevance and comprehensiveness
- Validate output format
- Show performance metrics
- Generate a summary report

**Expected Output:**
```
============================================================
ROAD SAFETY INTERVENTION EVALUATION TEST SUITE
============================================================
...
EVALUATION REPORT
============================================================

📊 Relevance Score: 85.00%
   Status: ✅ PASSED
   
📋 Comprehensiveness Score: 78.00%
   Status: ✅ PASSED
   
📝 Output Format Validation: ✅ PASSED

EVALUATION SUMMARY
============================================================
Total Queries Tested: 4
Relevance: Passed: 4/4 (100.0%)
Comprehensiveness: Passed: 4/4 (100.0%)
```

### 2. Run Pytest Test Suites

```bash
cd backend
pytest tests/ -v
```

This runs all test files:
- `test_evaluation_relevance.py` - Tests for accurate matching
- `test_evaluation_comprehensiveness.py` - Tests for detailed options
- `test_integration.py` - End-to-end integration tests
- `test_performance.py` - Performance benchmarks

### 3. Run Specific Test Categories

**Relevance Tests Only:**
```bash
pytest tests/test_evaluation_relevance.py -v
```

**Comprehensiveness Tests Only:**
```bash
pytest tests/test_evaluation_comprehensiveness.py -v
```

**Performance Tests Only:**
```bash
pytest tests/test_performance.py -v
```

### 4. Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

---

## Understanding Evaluation Metrics

### Relevance Score

Measures how accurately results match the query:
- **0.0-0.6**: Low relevance (results don't match well)
- **0.6-0.8**: Medium relevance (reasonable matches)
- **0.8-1.0**: High relevance (excellent matches)

**Factors:**
- Entity extraction match quality
- Query-to-intervention semantic similarity
- Filter match accuracy
- Confidence scores

### Comprehensiveness Score

Measures how detailed and complete the results are:
- **0.0-0.6**: Low comprehensiveness (missing details)
- **0.6-0.8**: Medium comprehensiveness (good details)
- **0.8-1.0**: High comprehensiveness (excellent details)

**Factors:**
- Number of results returned
- Detail level (specifications, IRC references, explanations)
- Category diversity
- Completeness of information

### Output Format Validation

Checks that results match evaluation criteria:
- ✅ Recommended interventions present
- ✅ Explanations include database references
- ✅ IRC references are valid
- ✅ All required fields are present

---

## Monitoring and Debugging

### Viewing Logs in Real-Time

```bash
# Backend logs (JSON format)
cd backend
uvicorn app.main:app --reload | jq .

# Or without jq (raw JSON)
uvicorn app.main:app --reload
```

### Filtering Logs by Request ID

If you have a request ID from an API response header:
```bash
# Search logs for specific request
grep "abc123-def456" backend/logs/app.log
```

### Analyzing Evaluation Metrics

All search queries log evaluation metrics. To analyze:

1. **Extract metrics from logs**:
   ```bash
   # Get all relevance scores
   grep "relevance_score" logs.txt | jq .relevance_score
   
   # Get all comprehensiveness scores
   grep "comprehensiveness_score" logs.txt | jq .comprehensiveness_score
   ```

2. **Track performance**:
   ```bash
   # Get query times
   grep "response_time_ms" logs.txt | jq .response_time_ms
   ```

---

## Troubleshooting

### Frontend Can't Connect to Backend

1. Check backend is running: `curl http://localhost:8000/health`
2. Verify API URL in frontend settings
3. Check API key is correct

### Tests Failing

1. **Ensure database is set up**:
   ```bash
   python backend/scripts/setup_database.py
   ```

2. **Check environment variables**:
   ```bash
   # Backend needs GEMINI_API_KEY
   echo $GEMINI_API_KEY
   ```

3. **Run tests with verbose output**:
   ```bash
   pytest tests/ -v -s
   ```

### Logs Not Showing

1. Check log level in `.env`:
   ```
   LOG_LEVEL=info
   ```

2. Verify structured logging is enabled (should be automatic)

---

## Next Steps

1. **Monitor Evaluation Metrics**: Watch relevance and comprehensiveness scores in logs
2. **Run Tests Regularly**: Use test suites to validate system performance
3. **Analyze Logs**: Use JSON logs to track system behavior
4. **Improve Based on Metrics**: Use evaluation scores to identify areas for improvement

---

## Quick Reference

### Start Everything
```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && streamlit run app.py

# Terminal 3: Run Tests
cd backend && pytest tests/ -v
```

### Check System Health
```bash
# Backend health
curl http://localhost:8000/health

# Frontend
open http://localhost:8501
```

### View Logs
```bash
# Backend logs (JSON format)
# Check terminal where backend is running
```

---

For more details, see the main README.md file.

