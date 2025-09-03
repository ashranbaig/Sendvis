# Sendvis 🚀  
**AI-powered agent to generate and send personalised pitch emails to recruiters**  

Sendvis is an intelligent agent that helps job seekers create customised email pitches for job opportunities. By providing the **job description**, **recruiter’s name**, and **recruiter’s email ID**, Sendvis generates a tailored pitch email and sends it directly from your **verified email address** using **SendGrid**.  


I am using two different agents(with different sets of instructions) and an evaluator, which will decide which email is better, and then you can send it directly to the recruiter.

---

## ✨ Features  
- 📄 **Smart Email Generation** – Creates professional and job-specific pitch emails.  
- 🧑‍💼 **Personalised Recruiter Targeting** – Adjusts tone and content using the recruiter’s name and role description.  
- 📧 **Secure Automated Sending via SendGrid** – Reliable email delivery with sender verification.  
- ⚙️ **Configurable & Secure** – Works with environment variables, no need to expose sensitive credentials.  

---

## 🔧 Tech Stack  
- **Language**: Python  
- **AI/LLM**: Used for generating pitch content (OpenAI)
- **Email Delivery**: SendGrid API  
- **Deployment**: Works locally or can be hosted on the cloud  

---

## 🚀 Getting Started  

### 1. Clone the repository  
git clone https://github.com/your-username/sendvis.git
cd sendvis


### 2. Install dependencies  
pip install -r requirements.txt


### 3. Configure environment variables  
Create a `.env` file in the root directory containing:  

SENDGRID_API_KEY=your_sendgrid_api_key

SENDER_EMAIL=your_verified_sendgrid_email@example.com(you can directly change it in the Sendgrid function)

OPENAI_API_KEY=your_ai_api_key_here



👉 Make sure to verify your **sender email** in SendGrid before sending.  

### 4. Run Sendvis  
