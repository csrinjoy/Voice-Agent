import os
import json
import traceback
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Professional AI Voice Agent", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class AgentChatRequest(BaseModel):
    message: str
    resume_context: str = ""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professional AI Voice Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    </script>
    <style>
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 25px rgba(59, 130, 246, 0.5), inset 0 0 15px rgba(59, 130, 246, 0.3); }
            50% { box-shadow: 0 0 45px rgba(59, 130, 246, 0.9), inset 0 0 25px rgba(59, 130, 246, 0.6); }
        }
        .orb-active { animation: pulse-glow 2s infinite ease-in-out; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">

    <div class="max-w-lg w-full bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-5">
        <div class="text-center">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-medium mb-2">
                <span class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span> Professional Voice Associate Live
            </span>
            <h1 class="text-2xl font-bold text-white">Interactive Voice Associate</h1>
            <p class="text-xs text-slate-400 mt-1">Upload your resume/profile and tap the orb to start speaking.</p>
        </div>

        <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-3">
            <div class="flex items-center justify-between">
                <label class="text-xs font-bold text-blue-400">
                    <i class="fa-solid fa-file-arrow-up mr-1"></i> Upload Profile / Resume:
                </label>
                <input type="file" id="resumeFile" accept=".pdf,.docx,.txt" onchange="handleFileUpload(event)" class="text-xs text-slate-400 file:mr-2 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer">
            </div>

            <div>
                <label class="block text-xs font-medium text-slate-400 mb-1">Or edit resume text directly:</label>
                <textarea id="resumeInput" rows="3" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 resize-none" placeholder="Paste background or resume here..."></textarea>
            </div>
            
            <button onclick="saveResumeContext()" class="w-full bg-slate-800 hover:bg-slate-700 text-blue-400 font-medium py-2 rounded-xl transition text-xs border border-slate-700">
                Update Knowledge Base
            </button>
        </div>

        <!-- Glowing Voice Orb UI -->
        <div class="relative flex items-center justify-center py-2">
            <div id="voiceOrb" onclick="handleOrbClick()" class="w-28 h-28 bg-slate-900 border-2 border-blue-500 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 shadow-2xl">
                <i id="orbIcon" class="fa-solid fa-microphone text-blue-400 text-3xl"></i>
            </div>
            <div id="orbRipple" class="absolute w-36 h-36 rounded-full border border-blue-500/30 pointer-events-none hidden animate-ping"></div>
        </div>

        <div id="agentStatus" class="bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-slate-300 min-h-[70px] flex flex-col items-center justify-center space-y-1 text-center">
            <span class="text-blue-400 font-bold">Ready</span>
            <span class="text-slate-400">Tap the orb to start the conversation.</span>
        </div>

        <div>
            <button onclick="toggleAgent()" id="actionBtn" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition flex items-center justify-center gap-2 text-sm">
                <i class="fa-solid fa-play"></i> Start Associate
            </button>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        const statusBox = document.getElementById('agentStatus');
        const voiceOrb = document.getElementById('voiceOrb');
        const orbRipple = document.getElementById('orbRipple');
        const orbIcon = document.getElementById('orbIcon');
        const actionBtn = document.getElementById('actionBtn');
        const resumeInput = document.getElementById('resumeInput');

        window.addEventListener('DOMContentLoaded', () => {
            const savedResume = localStorage.getItem('universal_agent_context');
            if (savedResume) {
                resumeInput.value = savedResume;
            } else {
                resumeInput.value = "John Doe: Senior Software Engineer with 6 years of expertise in cloud architecture, Python, and full-stack development.";
            }
        });

        function saveResumeContext() {
            const text = resumeInput.value.trim();
            localStorage.setItem('universal_agent_context', text);
            alert("Knowledge base updated successfully!");
        }

        function extractAgentName() {
            const text = resumeInput.value.trim();
            if (!text) return "Professional";
            const firstLine = text.split('\\n')[0].trim();
            const nameCandidate = firstLine.split(/[:,-]/)[0].trim();
            if (nameCandidate && nameCandidate.length < 25 && !nameCandidate.toLowerCase().includes('resume')) {
                return nameCandidate;
            }
            return "Professional";
        }

        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            const fileName = file.name.toLowerCase();
            statusBox.innerHTML = `<span class="text-blue-400 font-bold">Reading file...</span>`;

            try {
                if (fileName.endsWith('.docx')) {
                    const arrayBuffer = await file.arrayBuffer();
                    const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
                    resumeInput.value = result.value;
                    saveResumeContext();
                } else if (fileName.endsWith('.pdf')) {
                    const arrayBuffer = await file.arrayBuffer();
                    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                    let extractedText = "";
                    for (let i = 1; i <= pdf.numPages; i++) {
                        const page = await pdf.getPage(i);
                        const textContent = await page.getTextContent();
                        extractedText += textContent.items.map(item => item.str).join(' ') + "\\n";
                    }
                    resumeInput.value = extractedText;
                    saveResumeContext();
                } else if (fileName.endsWith('.txt')) {
                    const text = await file.text();
                    resumeInput.value = text;
                    saveResumeContext();
                } else {
                    alert("Please upload a valid .pdf, .docx, or .txt file.");
                }
            } catch (err) {
                console.error(err);
                alert("Error parsing file.");
            }
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;
        let isRunning = false;
        let selectedVoice = null;
        let lastTranscript = "";

        function loadVoices() {
            const voices = window.speechSynthesis.getVoices();
            selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.toLowerCase().includes('natural') || v.name.toLowerCase().includes('google') || v.name.toLowerCase().includes('premium'))) 
                       || voices.find(v => v.lang.startsWith('en')) 
                       || voices[0];
        }

        window.speechSynthesis.onvoiceschanged = loadVoices;
        loadVoices();

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                if (isRunning) setUIState('listening', 'Listening...');
            };

            recognition.onresult = (event) => {
                lastTranscript = event.results[0][0].transcript.toLowerCase().trim();
                // BARGE-IN: If user speaks while agent is talking, immediately cancel speech
                if (window.speechSynthesis.speaking) {
                    window.speechSynthesis.cancel();
                }
                setUIState('thinking', `Heard: "${lastTranscript}"`);
            };

            recognition.onend = () => {
                if (isRunning && lastTranscript.length > 0) {
                    const query = lastTranscript;
                    lastTranscript = "";
                    generateSmartAnswer(query);
                } else if (isRunning && statusBox.dataset.state === 'listening') {
                    setUIState('idle', 'Tap the orb to speak.');
                }
            };
        }

        function toggleAgent() {
            if (!isRunning) {
                isRunning = true;
                actionBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Associate`;
                playGreeting();
            } else {
                stopAgent();
            }
        }

        // BARGE-IN INTERACTION: Clicking orb anytime stops current speech and starts listening
        function handleOrbClick() {
            if (!isRunning) {
                toggleAgent();
            } else {
                if (window.speechSynthesis.speaking) {
                    window.speechSynthesis.cancel();
                }
                try { recognition.stop(); } catch(e){}
                setUIState('listening', 'Listening...');
                setTimeout(() => {
                    try { recognition.start(); } catch(e){}
                }, 150);
            }
        }

        function playGreeting() {
            const name = extractAgentName();
            const greeting = `Hello, I am ${name}'s AI agent, how can I help you today?`;
            setUIState('speaking', greeting);
            speakAsAgent(greeting, () => { startListeningSafely(); });
        }

        function startListeningSafely() {
            if (!isRunning) return;
            lastTranscript = "";
            setTimeout(() => {
                try { recognition.start(); } catch (e) {}
            }, 300);
        }

        async function generateSmartAnswer(query) {
            setUIState('thinking', `Processing inquiry...`);
            const currentResumeContext = resumeInput.value.trim();
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/agent-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: query, resume_context: currentResumeContext })
                });

                if (!response.ok) throw new Error(`Server error: ${response.status}`);

                const data = await response.json();
                const reply = data.reply || "I apologize, could you please repeat that?";

                setUIState('speaking', reply);
                speakAsAgent(reply, () => { startListeningSafely(); });

            } catch (err) {
                console.error(err);
                const errorReply = "I apologize, I am experiencing a temporary connection delay.";
                setUIState('speaking', errorReply);
                speakAsAgent(errorReply, () => { stopAgent(); });
            }
        }

        function speakAsAgent(text, callback) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            if (selectedVoice) utterance.voice = selectedVoice;
            utterance.rate = 1.05;
            utterance.pitch = 1.0;
            utterance.onend = () => { if (callback) callback(); };
            window.speechSynthesis.speak(utterance);
        }

        function setUIState(state, message) {
            statusBox.dataset.state = state;
            if (state === 'listening') {
                voiceOrb.classList.add('orb-active');
                orbRipple.classList.remove('hidden');
                orbIcon.className = "fa-solid fa-microphone-lines text-blue-400 text-3xl animate-pulse";
                statusBox.innerHTML = `<span class="text-blue-400 font-bold animate-pulse">Listening...</span><span class="text-slate-400 mt-1">${message}</span>`;
            } else if (state === 'speaking') {
                voiceOrb.classList.add('orb-active');
                orbRipple.classList.remove('hidden');
                orbIcon.className = "fa-solid fa-volume-high text-blue-400 text-3xl animate-bounce";
                statusBox.innerHTML = `<span class="text-blue-400 font-bold">Associate Speaking (Tap orb to interrupt):</span><span class="text-slate-300 mt-1">${message}</span>`;
            } else if (state === 'thinking') {
                voiceOrb.classList.remove('orb-active');
                orbRipple.classList.add('hidden');
                orbIcon.className = "fa-solid fa-headset text-blue-400 text-3xl animate-spin";
                statusBox.innerHTML = `<span class="text-amber-400 font-bold">Processing...</span><span class="text-slate-400 mt-1">${message}</span>`;
            } else {
                voiceOrb.classList.remove('orb-active');
                orbRipple.classList.add('hidden');
                orbIcon.className = "fa-solid fa-microphone text-blue-400 text-3xl";
                statusBox.innerHTML = `<span class="text-blue-400 font-bold">Ready</span><span class="text-slate-400">Tap the orb to start.</span>`;
            }
        }

        function stopAgent() {
            isRunning = false;
            window.speechSynthesis.cancel();
            if (recognition) { try { recognition.stop(); } catch(e){} }
            actionBtn.innerHTML = `<i class="fa-solid fa-play"></i> Start Associate`;
            setUIState('idle', 'Ready.');
        }
    </script>
</body>
</html>
    """

@app.post("/api/agent-chat")
def agent_chat(data: AgentChatRequest):
    context = data.resume_context.strip() if data.resume_context.strip() else "Professional background."
    
    system_instruction = (
        "You are a polite, professional call-center career associate representing the individual in the profile below. "
        "Answer questions naturally, professionally, and extremely concisely in strictly 1 short sentence."
    )
    
    user_content = f"Profile / Resume Context:\n{context}\n\nUser Question: {data.message}"
    
    # Direct REST API call to Google's Gemini endpoint (bypasses SDK blocking)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{user_content}"}]}
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 100
        }
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"API Error Response: {res.text}")
            raise HTTPException(status_code=500, detail=f"Gemini API Error: {res.status_code}")
            
        res_data = res.json()
        reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"reply": reply_text}
    except Exception as e:
        print("--- DIRECT API ERROR ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
