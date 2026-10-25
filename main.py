import os
import json
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Universal AI Voice Agent", version="3.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client pointing to Gemini's OpenAI-compatible endpoint
client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

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
    <title>Universal AI Voice Agent</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Mammoth.js for Word (.docx) parsing -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>
    <!-- PDF.js for PDF parsing -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    </script>
    <style>
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(234, 179, 8, 0.4), inset 0 0 15px rgba(234, 179, 8, 0.2); }
            50% { box-shadow: 0 0 40px rgba(234, 179, 8, 0.8), inset 0 0 25px rgba(234, 179, 8, 0.5); }
        }
        .orb-active { animation: pulse-glow 2s infinite ease-in-out; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">

    <div class="max-w-lg w-full bg-slate-800 border border-slate-700 rounded-3xl p-6 shadow-2xl space-y-5">
        
        <!-- Header -->
        <div class="text-center">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium mb-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Universal AI Voice Agent Live
            </span>
            <h1 class="text-2xl font-black text-yellow-400">Interactive Voice Assistant</h1>
            <p class="text-xs text-slate-400 mt-1">Upload a PDF/Word resume or paste text, then tap the orb to talk!</p>
        </div>

        <!-- File Upload Section -->
        <div class="bg-slate-900 border border-slate-700 rounded-2xl p-4 space-y-3">
            <div class="flex items-center justify-between">
                <label class="text-xs font-bold text-yellow-400">
                    <i class="fa-solid fa-file-arrow-up mr-1"></i> Upload Resume (PDF or DOCX):
                </label>
                <input type="file" id="resumeFile" accept=".pdf,.docx,.txt" onchange="handleFileUpload(event)" class="text-xs text-slate-400 file:mr-2 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-yellow-500 file:text-slate-900 hover:file:bg-yellow-400 cursor-pointer">
            </div>

            <div>
                <label class="block text-xs font-medium text-slate-400 mb-1">Or edit resume text directly:</label>
                <textarea id="resumeInput" rows="3" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-yellow-500 resize-none" placeholder="Paste resume background or bio here..."></textarea>
            </div>
            
            <button onclick="saveResumeContext()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-xl transition text-xs">
                Update Agent Knowledge Base
            </button>
        </div>

        <!-- Glowing Voice Orb UI -->
        <div class="relative flex items-center justify-center py-1">
            <div id="voiceOrb" onclick="handleOrbClick()" class="w-24 h-24 bg-slate-900 border-2 border-yellow-500 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 shadow-2xl">
                <i id="orbIcon" class="fa-solid fa-microphone text-yellow-400 text-2xl"></i>
            </div>
            <div id="orbRipple" class="absolute w-32 h-32 rounded-full border border-yellow-500/30 pointer-events-none hidden animate-ping"></div>
        </div>

        <!-- Dynamic Status Display -->
        <div id="agentStatus" class="bg-slate-900/80 border border-slate-700 rounded-2xl p-3 text-xs text-slate-300 min-h-[70px] flex flex-col items-center justify-center space-y-1 text-center">
            <span class="text-yellow-400 font-bold">Ready</span>
            <span class="text-slate-300">Upload a resume and tap the orb to start.</span>
        </div>

        <!-- Control Button -->
        <div>
            <button onclick="toggleAgent()" id="actionBtn" class="w-full bg-yellow-500 hover:bg-yellow-400 text-slate-900 font-bold py-3 px-4 rounded-xl shadow-lg transition flex items-center justify-center gap-2 text-sm">
                <i class="fa-solid fa-play"></i> Start Agent
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
                resumeInput.value = "Jane Doe: Software Engineer with 5 years of experience in Python, FastAPI, and React. Passionate about building AI tools.";
            }
        });

        function saveResumeContext() {
            const text = resumeInput.value.trim();
            localStorage.setItem('universal_agent_context', text);
            alert("Agent knowledge base updated successfully!");
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
                alert("Error parsing file. Please copy and paste text manually.");
            }
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;
        let isRunning = false;
        let selectedVoice = null;
        let lastTranscript = "";

        function loadVoices() {
            const voices = window.speechSynthesis.getVoices();
            selectedVoice = voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('male')) 
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
                if (isRunning) setUIState('listening', 'Listening... Speak your question now.');
            };

            recognition.onresult = (event) => {
                lastTranscript = event.results[0][0].transcript.toLowerCase().trim();
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
        } else {
            alert("Speech recognition requires Chrome, Edge, or Safari.");
        }

        function toggleAgent() {
            if (!isRunning) {
                isRunning = true;
                actionBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Agent`;
                playGreeting();
            } else {
                stopAgent();
            }
        }

        function handleOrbClick() {
            if (!isRunning) {
                toggleAgent();
            } else if (lastTranscript.length > 0) {
                const query = lastTranscript;
                lastTranscript = "";
                window.speechSynthesis.cancel();
                generateSmartAnswer(query);
            } else {
                try { recognition.stop(); } catch(e){}
                setTimeout(() => { recognition.start(); }, 200);
            }
        }

        function playGreeting() {
            const greeting = "Hello, I am your AI voice assistant. Ask me anything about the uploaded resume or background.";
            setUIState('speaking', greeting);
            speakAsAgent(greeting, () => {
                startListeningSafely();
            });
        }

        function startListeningSafely() {
            if (!isRunning) return;
            lastTranscript = "";
            setTimeout(() => {
                try { recognition.start(); } catch (e) {}
            }, 300);
        }

        async function generateSmartAnswer(query) {
            setUIState('thinking', `Thinking about: "${query}"...`);
            const currentResumeContext = resumeInput.value.trim();
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/agent-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: query,
                        resume_context: currentResumeContext 
                    })
                });

                if (!response.ok) throw new Error(`Server error: ${response.status}`);

                const data = await response.json();
                const reply = data.reply || "I couldn't generate a proper response.";

                setUIState('speaking', reply);
                speakAsAgent(reply, () => {
                    startListeningSafely();
                });

            } catch (err) {
                console.error(err);
                const errorReply = "Sorry, I ran into a connection issue with the secure server.";
                setUIState('speaking', errorReply);
                speakAsAgent(errorReply, () => { stopAgent(); });
            }
        }

        function speakAsAgent(text, callback) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            if (selectedVoice) utterance.voice = selectedVoice;
            utterance.rate = 1.0;
            utterance.pitch = 0.95;
            utterance.onend = () => { if (callback) callback(); };
            window.speechSynthesis.speak(utterance);
        }

        function setUIState(state, message) {
            statusBox.dataset.state = state;
            if (state === 'listening') {
                voiceOrb.classList.add('orb-active');
                orbRipple.classList.remove('hidden');
                orbIcon.className = "fa-solid fa-microphone-lines text-yellow-400 text-2xl animate-pulse";
                statusBox.innerHTML = `<span class="text-emerald-400 font-bold animate-pulse">Agent is listening...</span><span class="text-slate-300 mt-1">${message}</span>`;
            } else if (state === 'speaking') {
                voiceOrb.classList.add('orb-active');
                orbRipple.classList.remove('hidden');
                orbIcon.className = "fa-solid fa-volume-high text-yellow-400 text-2xl animate-bounce";
                statusBox.innerHTML = `<span class="text-yellow-400 font-bold">Agent Speaking:</span><span class="text-slate-300 mt-1">${message}</span>`;
            } else if (state === 'thinking') {
                voiceOrb.classList.remove('orb-active');
                orbRipple.classList.add('hidden');
                orbIcon.className = "fa-solid fa-brain text-yellow-400 text-2xl animate-spin";
                statusBox.innerHTML = `<span class="text-blue-400 font-bold">Agent processing...</span><span class="text-slate-300 mt-1">${message}</span>`;
            } else {
                voiceOrb.classList.remove('orb-active');
                orbRipple.classList.add('hidden');
                orbIcon.className = "fa-solid fa-microphone text-yellow-400 text-2xl";
                statusBox.innerHTML = `<span class="text-yellow-400 font-bold">Ready</span><span class="text-slate-300 mt-1">Upload a resume and tap the orb to start.</span>`;
            }
        }

        function stopAgent() {
            isRunning = false;
            window.speechSynthesis.cancel();
            if (recognition) { try { recognition.stop(); } catch(e){} }
            actionBtn.innerHTML = `<i class="fa-solid fa-play"></i> Start Agent`;
            setUIState('idle', 'Upload a resume and tap the orb to start.');
        }
    </script>
</body>
</html>
    """

@app.post("/api/agent-chat")
def agent_chat(data: AgentChatRequest):
    context = data.resume_context.strip() if data.resume_context.strip() else "No specific background provided. Be a helpful general assistant."
    
    system_prompt = (
        "You are a professional AI voice assistant representing the individual described in the resume or profile data below. "
        "Read their profile, identify their name, career history, skills, and background. "
        "Answer questions naturally, professionally, and concisely on their behalf as if speaking out loud in a voice conversation (keep responses under 3 sentences where possible).\n\n"
        f"--- PROFILE / RESUME DATA ---\n{context}\n-----------------------------"
    )
    
    try:
        response = client.chat.completions.create(
            model="gemini-1.5-flash",  # Switched to gemini-1.5-flash for universal compatibility
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        print("--- GEMINI API ERROR ---")
        traceback.print_exc()  # This prints the exact error into your Render Logs!
        raise HTTPException(status_code=500, detail=str(e))
