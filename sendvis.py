import os
import re
import asyncio
import gradio as gr
from dotenv import load_dotenv

# ---- your framework imports ----
from agents import Agent, Runner, trace, function_tool
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv(override=True)

# ==================== Writer Agent Instructions ====================
instructions1 = """
You are Mirza Mohd Ashran Baig, applying to a role. Write a professional email to the recruiter for the given Job Description (JD).

Inputs you will receive: {job_title}, {company}, {recruiter_name?}, and {jd_text}.
Addressing rule: If {recruiter_name} is provided, start with “Hi {recruiter_name}," and mention the name exactly once in the body. If not provided, start with “Hi,”.

Tone & length:
- Professional, confident, respectful
- 100–200 words
- Plain text only (no subject line, no markdown)

Structure:
1) Greeting
2) Short intro (state 5.5 years in DevOps/SRE)
3) 2–3 achievements/skills aligned to the JD (prefer measurable outcomes: uptime %, deployment time reduction, incident MTTR, automation wins, team leadership)
4) Interest in the role/company
5) One clear CTA (e.g., invite to discuss, request next steps)
6) Closing + signature

Hard requirements (do not forget):
- Sign with full name: Mirza Mohd Ashran Baig
- Include: LinkedIn: https://www.linkedin.com/in/ashranbaig/
- Include: Resume: https://drive.google.com/file/d/1lKJvC6sRMiYHpoRUQnz256YKZbSRxYy5/view?usp=drive_link
- Mirror 2–4 keywords from the JD; do not invent experience you don’t have.
- Keep language plain (no fluff/buzzwords/hedging). No placeholders like [Company].

- Never forget my name: Mirza Mohd Ashran Baig
- Add the linkedin profile link: https://www.linkedin.com/in/ashranbaig/
- Add the link to download my resume:https://drive.google.com/file/d/1lKJvC6sRMiYHpoRUQnz256YKZbSRxYy5/view?usp=drive_link

"""

instructions2 = """You are Mirza Mohd Ashran Baig, applying to a role. Write a concise recruiter email tailored to the JD.

Inputs: {job_title}, {company}, {recruiter_name?}, {jd_text}.
Greeting rule: If {recruiter_name} exists, start with “Hi {recruiter_name}," and mention it exactly once. Otherwise start with “Hi,”.

Constraints:
- 90–120 words (≤120)
- ≤2 short paragraphs + one-line closing
- 4–6 sentences total
- Include exactly ONE quantified achievement
- Mirror 2–3 JD keywords
- One clear CTA
- Plain text only (no subject line, no markdown)

Must include in closing:
- Full name: Mirza Mohd Ashran Baig
- LinkedIn: https://www.linkedin.com/in/ashranbaig/
- Resume: https://drive.google.com/file/d/1lKJvC6sRMiYHpoRUQnz256YKZbSRxYy5/view?usp=drive_link

"""

# ==================== Writer Agents ====================
sendvis_agent1 = Agent("Professional Sendvis Agent", instructions1, model="gpt-4o-mini")
sendvis_agent2 = Agent("Concise Sendvis Agent", instructions2, model="gpt-4o-mini")

# Convert to tools
tool1 = sendvis_agent1.as_tool("sendvis_agent1_tool", "Draft a professional recruiter email (100–200 words).")
tool2 = sendvis_agent2.as_tool("sendvis_agent2_tool", "Draft a concise recruiter email (≤120 words, one metric).")

# ==================== SendGrid as a Tool ====================
@function_tool
def send_email(body: str, to_address: str, subject: str = "Recruiter Outreach"):
    """Send out an email with the given body using SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return {"status": "error", "message": "SENDGRID_API_KEY not found."}

    if not to_address or not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", to_address.strip()):
        return {"status": "error", "message": f"Invalid recipient email: {to_address}"}

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email("ashranbaig1310@gmail.com")  # must be verified in SendGrid
        to_email = To(to_address.strip())
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content).get()
        resp = sg.client.mail.send.post(request_body=mail)
        return {"status": "success", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== Orchestrator ====================
orchestrator_instructions = """
You need to choose the best convincing email for the job application.

Steps:
1) Receive: JD, recruiter_name, recruiter_email, subject, send flag.
2) Make sure you add the name as Mirza Mohd Ashran Baig, Linkedin link and the Resume link in the end of the email.
3) Compare drafts: pick the one with better JD alignment, recruiter name usage (if provided), clarity, and recruiter appeal.
4) If send=true and recruiter_email provided, call send_email with the chosen draft, recruiter_email, and subject.
5)Must include after email sign-offs:
- Full name: Mirza Mohd Ashran Baig
- LinkedIn: https://www.linkedin.com/in/ashranbaig/
- Resume: https://drive.google.com/file/d/1lKJvC6sRMiYHpoRUQnz256YKZbSRxYy5/view?usp=drive_link

6) Return JSON only:
{
  "chosen_draft": "...",
  "sent": true/false,
  "send_result": { ... } | null
}
"""

orchestrator = Agent(
    name="Recruiter Email Orchestrator",
    instructions=orchestrator_instructions,
    tools=[tool1, tool2, send_email],
    model="gpt-4o-mini",
)

async def run_orchestration(jd_text: str, recruiter_name: str = "", recruiter_email: str = "",
                            subject: str = "Recruiter Outreach", send_flag: bool = False):
    payload = {
        "jd": jd_text,
        "recruiter_name": recruiter_name or "",
        "recruiter_email": recruiter_email or "",
        "subject": subject or "Recruiter Outreach",
        "send": bool(send_flag),
    }
    msg = str(payload)

    with trace("Orchestrate drafting"):
        res = await Runner.run(orchestrator, msg)
        raw = res.final_output.strip()

    import json
    try:
        data = json.loads(raw)
    except Exception:
        data = {"chosen_draft": raw, "sent": False, "send_result": None}

    data.setdefault("sent", False)
    data.setdefault("send_result", None)
    return data

# ==================== Gradio UI ====================
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

INITIAL_PROMPT = "Hi! Paste the **Job Description** (JD)."

def on_load():
    history = [("Please use the texbox below to enter the details", INITIAL_PROMPT)]
    state = {"jd": "", "recruiter_name": "", "email": "", "step": "await_jd", "last_draft": ""}
    return history, state, gr.update(value=""), gr.update(value="", interactive=False), gr.update(value="", interactive=False), gr.update(value="Application for SRE/DevOps role", interactive=False), gr.update(interactive=False)

def respond(user_message, chat_history, state):
    state = state or {"jd": "", "recruiter_name": "", "email": "", "step": "await_jd", "last_draft": ""}
    step = state.get("step", "await_jd")
    out_history = list(chat_history)
    def bot(msg): out_history.append(("assistant", msg))

    if step == "await_jd":
        jd = (user_message or "").strip()
        if len(jd) < 20:
            bot("Please paste the full JD (at least 20 characters).")
            return out_history, state, gr.update(value=""), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
        state["jd"] = jd
        state["step"] = "await_name"
        bot("Got the JD ✅\nNow provide the **recruiter’s name** (or type `skip`).")
        return out_history, state, gr.update(value=""), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

    if step == "await_name":
        text = (user_message or "").strip()
        if text.lower() not in {"skip", "none", ""}:
            state["recruiter_name"] = text
        state["step"] = "await_email"
        bot("Now provide the **recruiter’s email** (or type `skip`).")
        return out_history, state, gr.update(value=""), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

    if step == "await_email":
        text = (user_message or "").strip()
        m = EMAIL_RE.search(text)
        if m:
            state["email"] = m.group(0)
        elif text.lower() in {"skip", "none"}:
            state["email"] = ""
        state["step"] = "ready"
        bot("Thanks! Drafting your outreach now…")

    if state.get("step") == "ready":
        jd, name, email = state["jd"], state["recruiter_name"], state["email"]
        data = asyncio.run(run_orchestration(jd, recruiter_name=name, recruiter_email=email, send_flag=False))
        draft = data.get("chosen_draft", "")
        state["last_draft"] = draft
        bot(draft)
        bot("Would you like to **send Email**? Review and click Send.")
        return out_history, state, gr.update(value=""), gr.update(value=email, interactive=True), gr.update(value=name, interactive=True), gr.update(value="Application for SRE/DevOps role", interactive=True), gr.update(interactive=True)

    return out_history, state, gr.update(value=""), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

def on_send_click(to_value, name_value, subject_value, chat_history, state):
    out_history = list(chat_history)
    jd, draft = state.get("jd", ""), state.get("last_draft", "")
    to_addr, name, subject = (to_value or "").strip(), (name_value or "").strip(), (subject_value or "Recruiter Outreach").strip()
    if not draft:
        out_history.append(("assistant", "No draft to send."))
        return out_history, gr.update(interactive=True)
    data = asyncio.run(run_orchestration(jd, recruiter_name=name, recruiter_email=to_addr, subject=subject, send_flag=True))
    if data.get("sent") and data.get("send_result", {}).get("status") == "success":
        out_history.append(("assistant", f"✅ Email sent to {to_addr} (status {data['send_result'].get('code')})."))
        return out_history, gr.update(interactive=False)
    else:
        out_history.append(("assistant", f"⚠️ Send failed.\nDetails: {data.get('send_result')}"))
        return out_history, gr.update(interactive=True)

# ==================== Launch ====================
with gr.Blocks(title="Recruiter Email Assistant") as demo:
    gr.Markdown("## Recruiter Email Assistant\nJD → Recruiter name → Email → Draft → Send via SendGrid")

    chatbot = gr.Chatbot(height=440)
    user_input = gr.Textbox(placeholder="Paste it here first…", show_label=False)

    gr.Markdown("---")

    with gr.Row():
        to_box = gr.Textbox(label="Recruiter Email", interactive=False)
        name_box = gr.Textbox(label="Recruiter Name", interactive=False)
        subject_box = gr.Textbox(label="Subject", value="Application for Senior SRE/DevOps role with 5.5+ years of Experience", interactive=False)
    with gr.Row():
        send_btn = gr.Button("Send via SendGrid", variant="primary", interactive=False)

    state = gr.State({})

    demo.load(on_load, None, [chatbot, state, user_input, to_box, name_box, subject_box, send_btn])
    user_input.submit(respond, [user_input, chatbot, state], [chatbot, state, user_input, to_box, name_box, subject_box, send_btn])
    send_btn.click(on_send_click, [to_box, name_box, subject_box, chatbot, state], [chatbot, send_btn])

if __name__ == "__main__":
    demo.launch()
