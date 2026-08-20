# Testing Documentation

To ensure the reliability of the MediScope platform, multiple testing strategies were employed across the stack.

## 1. Manual Testing Workflow
Manual testing was conducted simulating an end-to-end user journey:
1. **Trigger Scraper**: Manually execute `scrapy crawl who_spider` and verify new documents appear in MongoDB `raw_articles`.
2. **Trigger Processor**: Run `python -m backend.pipeline.processor`. Observe terminal output to ensure NLP extraction identifies diseases correctly.
3. **Verify Database**: Check MongoDB Atlas UI to ensure records are created in `outbreaks_v2` and that `case_counts` are appended.
4. **UI Validation**: Open `http://localhost:5173`. Verify that the newly processed outbreak appears on the map in the correct geographic location. Check the `Analytics` page to ensure the bar charts updated.

## 2. API Testing (Postman/cURL)
The Flask REST API was tested independently of the frontend to ensure robust error handling.
- **Valid Requests**: `GET /api/outbreaks?disease=cholera`. Verified the response is HTTP 200 and the JSON array only contains Cholera records.
- **Invalid Requests**: Tested with malformed query parameters and verified the `_handle_errors` decorator gracefully caught exceptions and returned HTTP 500 JSON payloads instead of crashing the server.

## 3. Database Testing
- **Index Verification**: Attempted to insert duplicate records into `outbreaks_v2` manually. Verified that the Compound Index rejected exact duplicates.
- **Data Integrity**: Used MongoDB Compass to ensure no `ObjectId` references were broken and that the `pubDate` fields were properly cast to ISO dates.

## 4. Frontend Testing
- **Responsive Design**: Resized the browser window to mobile width. Verified that Tailwind CSS media queries correctly collapsed the Sidebar filters and resized the Leaflet map container.
- **State Management**: Rapidly toggled filters on the `Map.jsx` page to ensure React state updated cleanly and Axios requests were not infinitely looping.

## Suggested Future Tests (Unit & Integration)
While the current testing was primarily manual and exploratory, a production-grade system should implement automated test suites:
- **PyTest (Backend)**: Write unit tests for `ner.py` providing strings like "Ebola in Congo" and asserting `extract_entities()` returns exactly `['ebola']` and `['DR Congo']`.
- **Jest / React Testing Library (Frontend)**: Mock the Axios API calls and verify that `Map.jsx` renders the correct number of Leaflet `<Marker>` components based on the mocked JSON response.
