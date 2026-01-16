# Gemini API Quota Management Guide

## Understanding the Quota Limits

The Gemini free tier has the following limits:
- **20 requests per day** for `gemini-flash-latest`
- Quota resets every 24 hours
- Each interview session uses multiple API calls:
  - 2 calls to start (initialize + opening question)
  - 1 call per user response
  - 1 call for final report generation

## Current API Call Counter

The system now tracks API calls with console output:
```
🔢 API Call #1 - reset_session
🔢 API Call #2 - opening question
🔢 API Call #3 - get_response
```

## Solutions When You Hit the Quota

### Option 1: Wait for Quota Reset
The quota resets 24 hours after your first request of the day. Check the error message for the exact retry time.

### Option 2: Use Development Mode (Recommended for Testing)

Enable DEV_MODE to use mock AI responses without consuming API quota:

1. Open `.env` file
2. Change `DEV_MODE=false` to `DEV_MODE=true`
3. Restart the backend server

In DEV_MODE:
- ✅ All features work normally
- ✅ Eye tracking and metrics still function
- ✅ No API calls are made
- ✅ Mock responses are contextually appropriate
- ⚠️ AI responses are generic (not personalized)

### Option 3: Use a Different API Key

If you have multiple Google accounts:
1. Create a new API key at https://aistudio.google.com/app/apikey
2. Update `GOOGLE_API_KEY` in `.env`
3. Restart the backend

### Option 4: Optimize API Usage

To reduce API calls during development:
- Use DEV_MODE for frontend/UI testing
- Only disable DEV_MODE when testing AI conversation quality
- Test with shorter interviews
- Avoid refreshing the interview page (causes re-initialization)

## Preventing Double Initialization

The frontend now prevents React Strict Mode from causing double initialization:
```typescript
const [isInitialized, setIsInitialized] = useState(false);

useEffect(() => {
  if (isInitialized) return; // Prevent double init
  setIsInitialized(true);
  initializeInterview();
}, []);
```

## Error Messages Explained

### Error: "models/gemini-1.5-flash is not found"
This happens when the API tries to use an old model name. The code now uses `gemini-flash-latest` everywhere.

### Error: "Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests"
You've hit the 20 requests/day limit. Use DEV_MODE or wait for quota reset.

### Error: "Please retry in X seconds"
The error message tells you exactly when your quota will reset.

## Best Practices

1. **Development**: Use `DEV_MODE=true` for all UI/UX testing
2. **AI Testing**: Disable DEV_MODE only when testing conversation quality
3. **Production**: Keep DEV_MODE=false and monitor API usage
4. **Monitoring**: Watch console for API call counter to track usage

## Upgrading to Paid Tier

If you need more quota:
1. Visit https://ai.google.dev/pricing
2. Enable billing on your Google Cloud project
3. Paid tier offers 1500 requests per day
