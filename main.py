import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Universal AI Voice Agent Backend", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class AIAuditRequest(BaseModel):
    business_name: str
    industry: str
    city: str

class SchemaRequest(BaseModel):
    business_name: str
    industry: str
    address: str
    phone: str
    website: str
    city: str

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
        <title>Universal AI Voice Agent Backend</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl space-y-4">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Backend Online & Universal
            </span>
            <h1 class="text-2xl font-black text-white">Universal Voice Agent API</h1>
            <p class="text-xs text-slate-400">Ready to power custom voice agents for any resume or document.</p>
        </div>
    </body>
    </html>
    """

@app.post("/api/audit-ai-visibility")
def audit_ai_visibility(data: AIAuditRequest):
    prompt = (
        f"Act as a local consumer search engine. A user asks: 'What are the top 3 best {data.industry} "
        f"businesses in {data.city}? Give me specific names.'\n\n"
        f"Analyze your response knowledge base for {data.city} {data.industry}. "
        f"Is '{data.business_name}' explicitly recommended? Answer strictly in JSON format with keys: "
        f"'is_mentioned' (boolean), 'competitors_listed' (list of strings), and 'recommendation_summary' (string)."
    )
    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {"target_business": data.business_name, "location": data.city, "audit_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-ai-schema")
def generate_ai_schema(data: SchemaRequest):
    schema_markup = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": data.business_name,
        "description": f"Top-rated {data.industry} serving {data.address}.",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": data.address,
            "addressLocality": data.city,
            "addressCountry": "US"
        },
        "telephone": data.phone,
        "url": data.website,
        "priceRange": "$$"
    }
    return {"instructions": "Paste this JSON-LD script inside the <head> tag.", "json_ld": schema_markup}

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
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))