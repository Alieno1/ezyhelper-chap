# EzyHelpers CHAP: Executive Pitch & Interview Preparation Guide
*(Written in Plain, Simple Language for Your Meeting with Arun & Leadership)*

**Author:** **Himanshu Singh** (AI Backend Engineer | NIT Surat CSE Graduate)  
**LinkedIn:** [linkedin.com/in/himanshu-singh-7ab162243](https://www.linkedin.com/in/himanshu-singh-7ab162243/) | **Portfolio:** [hud-portfolio.vercel.app](https://hud-portfolio.vercel.app/)

---

## 1. The 30-Second Elevator Pitch
> *"When you ask: 'What did you build?'"*

**Say this:**
> "I built an autonomous AI onboarding platform for our internal CRM called **CHAP (Customer Helper Admin Platform)**. 
> 
> Right now, domestic helpers—like maids and cooks—never fill out long 50-field registration forms on mobile apps. Recruiters have to call hundreds of numbers from job portals manually, which costs thousands of rupees and takes weeks. 
> 
> Our system reverses that: **AI pre-fills 80% of the helper's profile automatically from messy job portal resumes**, engages them on **WhatsApp with quick-reply buttons and a Free Digital Resume**, runs **instant KYC identity checks**, and **auto-routes Field Officers in Bangalore** to create a verified customer docket. 
> 
> It drops the Cost of Acquisition (CAC) down to **₹1,000 per verified helper**, and is already deployed live on Vercel and Render with a cloud PostgreSQL database."

---

## 2. The Real-World Story: Before vs. After

### Before (The Manual Way)
* Recruiter buys a pack of 50 numbers on Apna or WorkIndia.
* Recruiter calls all 50 people. Most don't pick up.
* For the few who answer, recruiter spends 20 minutes asking: *"Do you cook non-veg? What time do you sleep? How much salary do you want?"*
* Recruiter manually types all of this into Excel.
* A field agent is dispatched on a bike to find their house.
* **Cost:** ₹3,000 to ₹5,000 per onboarded helper. **Time:** 7 to 14 days.

### After (What Your Software Does)
* The agent automatically unlocks the 50 leads.
* An AI LLM reads their messy bios and extracts their full 5-step profile with shift times, skills, and do's & don'ts into PostgreSQL (**80% complete** before a human ever touches it).
* The bot sends a friendly WhatsApp message in Hindi. When the helper taps *"Yes, I want a job"*, the system gives her a **Free Branded Digital Resume** (the trust-building hook).
* The helper agrees to KYC on WhatsApp → gets a **Blue Tick (✓)**.
* Bangalore helpers are automatically assigned to **Field Officer Client** with geo-coordinates.
* **Cost:** Exact **₹1,000 CAC**. **Time:** 30 seconds.

---

## 3. Step-by-Step Live Demo Script (What to Click & What to Say)

Open your live website: **`https://ezyhelper-chap.vercel.app`**

### Step 1: Show the CAC Funnel Cards (Top Bar)
* **What to say:** *"Arun, at the very top, we give management real-time unit economics. You can see we spent ₹2,000 on Apna and WorkIndia, unlocked 50 contacts at ₹40 each, got 10 WhatsApp active replies, 5 active job seekers, and 2 Bangalore conversions. That gives us a verified CAC of exactly ₹1,000 per helper."*

### Step 2: Show the Dual Operating Modes
* **What to say:** *"In the Agent Control Center, we built two modes:"*
  * **Option A: `⚡ Run Full Autopilot (Zero Clicks)`**
    * Click this button.
    * *"Watch the live terminal: it searches portals, extracts the profiles with AI, sends WhatsApp pings, and automatically awards the Blue Tick and assigns Field Officer Client. In 30 seconds, every candidate docket is finished with zero manual clicks."*
  * **Option B: `▶ Interactive Mode (Manual Step-by-Step)`**
    * *"If a manager wants human oversight, this mode lets you test each verification step manually."*

### Step 3: Demonstrate the Helper Experience (The Partner App Emulator)
* Click the blue **"Partner App"** button on **Rita Das**.
* **What to say:** *"Our system also thinks about the helper. When Rita opens her phone, she doesn't see an empty form. She sees that 80% of her profile is already filled! She can toggle her availability, share her referral code `WXWRSH` for a ₹500 bonus, and click **'Resume Dekhiye'**."*
* Click **"Resume Dekhiye"**:
* *"This opens her professional EzyHelpers Branded Digital CV. She can print it or save it as a PDF. This free CV is why helpers love and trust EzyHelpers."*

### Step 4: Run the Customer Propensity Matcher
* Click the **"Customer Propensity Matcher"** tab.
* Click the button: **`Bengali Family – HSR Layout`**.
* Click **"Match"**.
* **What to say:** *"When a customer calls looking for a cook in HSR Layout who cooks fish and sleeps by 10 PM, our matcher instantly scores candidates. Rita Das matches at 83% because she lives in HSR Layout, cooks fish curry, and sleeps at 10 PM. The AI even gives the recruiter an operational tip: 'Strong match — shortlist now'."*

---

## 4. Likely Interview Questions & Winning Answers

### Q1: "Why did you build two modes: Autopilot and Interactive?"
> **Your Answer:** *"In full production, you want 100% Autopilot so zero human labor is wasted on repetitive data entry. But in real-world operations, leaders and managers want 'Human-in-the-Loop' oversight—for instance, deciding when to send a field officer. Having both demonstrates full autonomous capability while giving managers operational control."*

### Q2: "Why use PostgreSQL on Neon instead of a simple local database like SQLite?"
> **Your Answer:** *"Serverless hosting platforms like Vercel and Render are stateless—every time they restart or redeploy, local files like SQLite are wiped clean. To make this production-grade and ensure we never lose candidate KYC or CRM records during an executive demo, I used a managed PostgreSQL 16 database on Neon in Singapore. Our backend even has an automatic SQLite fallback so it never crashes if the internet drops."*

### Q3: "How does the AI handle messy text without making mistakes (hallucinating)?"
> **Your Answer:** *"Raw resumes from job portals are written in informal Hinglish with lots of slang. We send the raw text to the LLM with strict instructions to output structured JSON matching EzyHelpers' 5-step schema. In our backend, we use Pydantic v2 to enforce strict validation—normalizing gender, work types, and roles—so invalid data can never corrupt our database."*

### Q4: "How does this lower our Customer Acquisition Cost (CAC) to ₹1,000?"
> **Your Answer:** *"Today, telecallers spend hours calling cold leads who never answer, wasting paid portal credits. Our system uses a low-cost automated funnel: ₹2,000 buys 50 portal credits. WhatsApp automation quickly filters out the 40 people who aren't interested. Only serious, Bangalore-ready candidates are pushed to the final verification stage, yielding a predictable ₹1,000 acquisition cost."*

### Q5: "How do you handle privacy and government regulations around Aadhaar?"
> **Your Answer:** *"Under UIDAI regulations in India, storing raw 12-digit Aadhaar numbers without a certified vault is illegal. Our system strictly adheres to privacy compliance by tokenizing and masking the ID as `[Aadhaar Redacted]` in our database. We store the verification status and audit timestamp, never the sensitive raw number."*

---

## 5. Key Vocabulary Cheat Sheet

| Term | What it means |
| :--- | :--- |
| **CHAP** | **Customer Helper Admin Platform** (EzyHelpers' internal CRM for operations). |
| **HLPRINxxxxx** | The unique Helper ID format used inside EzyHelpers (e.g., `HLPRIN52445`). |
| **CAC** | **Customer Acquisition Cost** (how much money was spent to onboard one ready helper). |
| **Blue Tick KYC** | Verified identity badge powered by automated Digio/UIDAI consent checks. |
| **FO Geo-Docket** | An in-person address verification where Field Officer Client verifies the candidate's home with geo-coordinates. |
| **Propensity Score** | A 0–100% compatibility score matching a customer's specific household rules with a helper's preferences. |

