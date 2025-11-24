# Volunteer Finder - AI Automation Feature

## Overview

This branch implements AI-powered two-way matching between volunteers and opportunities using OpenAI's GPT-4o-mini model.

### Key Features

- **Automatic Resume Scoring**: When a volunteer uploads a resume, it's automatically scored against all active opportunities
- **Automatic Opportunity Scoring**: When an organization creates an opportunity, all existing resumes are scored against it
- **Personalized Matching**: Volunteers see their Top 5 matching opportunities; Organizations see Top 10 matching candidates
- **Candidate Management**: Organizations can Accept, Reject, or Waitlist candidates directly from the interface
- **ADMIN MANAGEMENT**: Administrators can monitor changes within the system when opportunities and resumes are deleted and chnaged

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- Django 4.2+
- OpenAI API Key

### 1. Clone and Checkout Branch
```bash
git clone <https://github.com/bretterer/volunteer-finder>
cd volunteer-finder
git checkout AI_Automation
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=(contact Matthew Sheaffer for access)
DEBUG=True
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the Server
```bash
python manage.py runserver
```

---

## How It Works

### Volunteer Flow

1. Volunteer logs in and navigates to **My Resume**
2. Uploads a resume (DOCX, PDF, or TXT)
3. System automatically:
   - Extracts text from the file
   - Scores resume against all active opportunities using AI
   - Displays personalized Top 5 matches

### Organization Flow

1. Organization logs in and creates a new opportunity
2. System automatically:
   - Scores all existing resumes against the new opportunity
3. Organization views opportunity detail page to see:
   - Top 10 matching candidates with scores
   - Accept/Reject/Waitlist buttons for each candidate

---

## Files Changed/Created

### Resumes App

| File | Description |
|------|-------------|
| `resumes/models.py` | Resume and ResumeScore models with auto text extraction and grading |
| `resumes/views.py` | Upload, view, and delete resume views with transaction handling |
| `resumes/signals.py` | Signal to auto-score resumes when opportunities are created |
| `resumes/services.py` | ResumeScoringService - AI integration with OpenAI |
| `resumes/admin.py` | Admin interface for Resume and ResumeScore |

### Opportunities App

| File | Description |
|------|-------------|
| `opportunities/views.py` | Added top_candidates to detail view, candidate status updates |
| `opportunities/urls.py` | Added URL for update_candidate_status |

### Templates

| File | Description |
|------|-------------|
| `templates/opportunities/list.html` | Added "Your Top 5 Matches" section for volunteers |
| `templates/opportunities/detail.html` | Added "Top 10 Candidates" table with action buttons |
| `templates/resumes/my_resume.html` | Resume dashboard with opportunity matches |
| `templates/resumes/upload.html` | Resume upload form |
| `templates/base.html` | Added "My Resume" navigation link |

### Other

| File | Description |
|------|-------------|
| `accounts/models.py` | Added `name` property to User model |
| `notifications/signals.py` | Fixed organization reference in email notifications |

---

## Grading Scale

| Score | Grade |
|-------|-------|
| 98-100% | A+ |
| 94-97% | A |
| 90-93% | A- |
| 85-89% | B+ |
| 80-84% | B |
| 74-79% | B- |
| 68-73% | C+ |
| 62-67% | C |
| 56-61% | C- |
| 50-55% | D+ |
| 44-49% | D |
| 0-43% | D- |

---

## Key URLs

| URL | Description |
|-----|-------------|
| `/resumes/upload/` | Upload resume (volunteers) |
| `/resumes/my-resume/` | View resume and matches (volunteers) |
| `/opportunities/list/` | Browse opportunities with Top 5 matches |
| `/opportunities/create/` | Create new opportunity (organizations) |
| `/opportunities/<id>/` | View opportunity details with Top 10 candidates |

---

## API Integration

### OpenAI Configuration

The system uses OpenAI's GPT-4o-mini model for scoring. Configuration is in `resumes/services.py`:
```python
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    response_format={"type": "json_object"}
)
```

### Scoring Dimensions

The AI evaluates resumes on:
- **Overall Score** (0-100): Combined assessment
- **Skills Match** (0-100): Technical skills alignment
- **Experience Match** (0-100): Relevant experience
- **Education Match** (0-100): Educational background fit

---

## Testing

### Manual Testing

1. **Test Volunteer Upload:**
```bash
   python manage.py runserver
   # Login as volunteer, upload resume, check terminal for scoring output
```

2. **Test Opportunity Creation:**
```bash
   # Login as organization, create opportunity, check terminal for scoring output
```

3. **Verify Scores in Shell:**
```bash
   python manage.py shell
```
```python
   from resumes.models import ResumeScore
   ResumeScore.objects.filter(opportunity_id=109).order_by('-overall_score')[:10]
```

---

## Troubleshooting

### Common Issues

**1. Text extraction fails:**
- Ensure `python-docx` and `PyPDF2` are installed
- Check file permissions in media folder

**2. Scoring not triggering:**
- Verify OpenAI API key is set
- Check terminal for error messages
- Ensure resume has extracted_text populated

**3. Grades showing incorrectly:**
- Run: `python manage.py shell`
- Execute: `for s in ResumeScore.objects.all(): s.save()`

---

## Contributors

- University of Michigan Dearborn - SWE553 Team

---

## License

This project is for educational purposes as part of the SWE553 course.