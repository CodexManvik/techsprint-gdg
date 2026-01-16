# Audio Setup Guide - Interview Mirror

## Quick Summary

Your app now supports **TWO audio modes**:

1. **Browser Speech** (Default for Chrome/Edge/Safari) - FREE, instant, no setup
2. **Backend Processing** (Default for Firefox) - Requires Google Cloud setup

## Browser Compatibility

| Browser | Browser Speech | Backend Mode |
|---------|---------------|--------------|
| Chrome  | ✅ Yes        | ✅ Yes       |
| Edge    | ✅ Yes        | ✅ Yes       |
| Safari  | ✅ Yes        | ✅ Yes       |
| Firefox | ❌ No         | ✅ Yes       |

## Option 1: Browser Speech (Recommended for Demo)

**Pros:**
- Zero setup required
- Works instantly
- Free forever
- Low latency
- Works offline

**Cons:**
- Only works in Chrome, Edge, Safari
- Firefox users must use backend mode

**Setup:** None! Just use Chrome/Edge/Safari

## Option 2: Backend Processing (For Production)

**Pros:**
- Works on ALL browsers (including Firefox)
- Higher quality transcription
- More control over voice profiles
- Professional TTS voices

**Cons:**
- Requires Google Cloud account
- Costs money (but has free tier)
- Requires credentials setup

### Backend Setup Steps:

#### 1. Create Google Cloud Project (5 minutes)

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable these APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API

#### 2. Create Service Account (3 minutes)

1. Go to IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Name it "interview-mirror"
4. Grant roles:
   - Cloud Speech Client
   - Cloud Text-to-Speech Client
5. Click "Create Key" → JSON
6. Download the JSON file

#### 3. Add Credentials to Project (1 minute)

```bash
# Rename the downloaded file to google_credentials.json
# Place it in your project root:
cp ~/Downloads/your-project-xxxxx.json google_credentials.json
```

#### 4. Restart Backend

```bash
python app.py
```

You should see:
```
✅ Found credentials at: /path/to/google_credentials.json
✅ STT: Google Cloud Speech-to-Text Connected
✅ TTS: Google Cloud Text-to-Speech Connected
```

## Fallback Behavior

Your backend is smart! It has **automatic fallbacks**:

1. **Google Cloud** (if credentials exist) → Best quality
2. **SpeechRecognition + gTTS** (if no credentials) → Basic quality
3. **Browser Speech** (if backend fails) → Client-side processing

## Cost Estimate (Google Cloud)

**Free Tier (Monthly):**
- Speech-to-Text: 60 minutes free
- Text-to-Speech: 1 million characters free

**After Free Tier:**
- Speech-to-Text: $0.006 per 15 seconds (~$1.44/hour)
- Text-to-Speech: $4 per 1 million characters

**For a 2-hour demo:** Likely stays within free tier!

## Testing Your Setup

### Test Browser Speech:
1. Open app in Chrome
2. Go to Lobby → Select "Browser Speech"
3. Start interview
4. Speak - you should see transcript appear instantly

### Test Backend Mode:
1. Open app in any browser
2. Go to Lobby → Select "Server Processing"
3. Start interview
4. Speak - backend will process and respond

## Troubleshooting

### "Speech recognition not supported"
- **Solution:** Use Chrome, Edge, or Safari, OR switch to Backend mode

### "Backend mode not working"
- **Check:** Is `google_credentials.json` in project root?
- **Check:** Did you enable the APIs in Google Cloud?
- **Check:** Restart the backend after adding credentials

### "No audio playing"
- **Browser mode:** Check browser console for errors
- **Backend mode:** Check backend logs for TTS errors

## Recommended for Your Demo

**For 2-hour prototype:**
1. Use **Browser Speech mode** in Chrome/Edge
2. Keep Backend mode as backup for Firefox users
3. Don't worry about Google Cloud unless you need Firefox support

**Why?**
- Browser speech works instantly
- No setup required
- Perfect for demos
- Can add Google Cloud later if needed

## Current Status

✅ Frontend: Fully implemented with mode selector
✅ Backend: Supports both modes with fallbacks
✅ Auto-detection: Switches to backend if browser doesn't support speech
✅ Error handling: Graceful fallbacks at every level

You're ready to demo! 🚀
