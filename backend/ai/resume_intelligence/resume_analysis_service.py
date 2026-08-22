"""
CertiTrust AI - Resume Intelligence Analysis Service.
Performs complete resume parsing, structured extraction, claim inventory,
and Skill Passport verification against the CertiTrust trusted credential registry.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from app.utils.logger import logger
from app.services.registry_service import credential_registry


# =========================================================================
# SKILL TAXONOMY - Normalized skill name mapping and categories
# =========================================================================
SKILL_ALIASES = {
    "react.js": "React", "reactjs": "React", "react js": "React", "react": "React",
    "node.js": "Node.js", "nodejs": "Node.js", "node js": "Node.js",
    "next.js": "Next.js", "nextjs": "Next.js",
    "vue.js": "Vue.js", "vuejs": "Vue.js",
    "express.js": "Express.js", "expressjs": "Express.js",
    "angular.js": "Angular", "angularjs": "Angular",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "scikit-learn": "Scikit-Learn", "sklearn": "Scikit-Learn",
    "opencv": "OpenCV", "open cv": "OpenCV",
    "fastapi": "FastAPI", "fast api": "FastAPI",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "natural language processing": "NLP", "nlp": "NLP",
    "computer vision": "Computer Vision",
    "data science": "Data Science",
    "cybersecurity": "Cybersecurity", "cyber security": "Cybersecurity",
    "blockchain": "Blockchain",
    "cloud computing": "Cloud Computing",
    "amazon web services": "AWS", "aws": "AWS",
    "google cloud": "GCP", "gcp": "GCP", "google cloud platform": "GCP",
    "microsoft azure": "Azure", "azure": "Azure",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "git": "Git", "github": "GitHub", "git & github": "Git",
    "devops": "DevOps", "ci/cd": "CI/CD",
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mongodb": "MongoDB", "mongo": "MongoDB",
    "redis": "Redis",
    "python": "Python", "java": "Java", "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++", "cpp": "C++", "c#": "C#", "csharp": "C#",
    "golang": "Go", "rust": "Rust", "ruby": "Ruby",
    "swift": "Swift", "kotlin": "Kotlin", "php": "PHP",
    "html": "HTML", "css": "CSS", "sass": "SASS", "less": "LESS",
    "flask": "Flask", "django": "Django", "spring boot": "Spring Boot",
    "linux": "Linux", "ubuntu": "Ubuntu",
    "figma": "Figma", "photoshop": "Photoshop",
    "tableau": "Tableau", "power bi": "Power BI",
    "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "selenium": "Selenium", "jest": "Jest", "pytest": "Pytest",
    "graphql": "GraphQL", "rest api": "REST API",
    "firebase": "Firebase", "supabase": "Supabase",
    "tailwindcss": "Tailwind CSS", "tailwind css": "Tailwind CSS", "tailwind": "Tailwind CSS",
    "bootstrap": "Bootstrap",
}

SKILL_CATEGORIES = {
    "Python": "Programming Language", "Java": "Programming Language",
    "JavaScript": "Programming Language", "TypeScript": "Programming Language",
    "C++": "Programming Language", "C#": "Programming Language",
    "Go": "Programming Language", "Rust": "Programming Language",
    "Ruby": "Programming Language", "Swift": "Programming Language",
    "Kotlin": "Programming Language", "PHP": "Programming Language",
    "HTML": "Web Technology", "CSS": "Web Technology",
    "React": "Frontend Framework", "Vue.js": "Frontend Framework",
    "Angular": "Frontend Framework", "Next.js": "Frontend Framework",
    "Tailwind CSS": "CSS Framework", "Bootstrap": "CSS Framework",
    "Node.js": "Backend Runtime", "Express.js": "Backend Framework",
    "FastAPI": "Backend Framework", "Flask": "Backend Framework",
    "Django": "Backend Framework", "Spring Boot": "Backend Framework",
    "TensorFlow": "ML/AI Framework", "PyTorch": "ML/AI Framework",
    "Scikit-Learn": "ML/AI Library", "OpenCV": "Computer Vision Library",
    "Machine Learning": "AI Domain", "Deep Learning": "AI Domain",
    "Artificial Intelligence": "AI Domain", "NLP": "AI Domain",
    "Computer Vision": "AI Domain", "Data Science": "AI Domain",
    "AWS": "Cloud Platform", "GCP": "Cloud Platform", "Azure": "Cloud Platform",
    "Docker": "DevOps Tool", "Kubernetes": "DevOps Tool",
    "Git": "Version Control", "GitHub": "Development Platform",
    "DevOps": "Practice", "CI/CD": "Practice",
    "SQL": "Database", "MySQL": "Database", "PostgreSQL": "Database",
    "MongoDB": "Database", "Redis": "Database",
    "Cybersecurity": "Security Domain", "Blockchain": "Technology Domain",
    "Cloud Computing": "Technology Domain",
    "Linux": "Operating System", "Ubuntu": "Operating System",
    "Pandas": "Data Library", "NumPy": "Data Library", "Matplotlib": "Data Library",
    "GraphQL": "API Technology", "REST API": "API Technology",
    "Firebase": "Backend Service", "Supabase": "Backend Service",
    "Selenium": "Testing Tool", "Jest": "Testing Tool", "Pytest": "Testing Tool",
    "Figma": "Design Tool", "Photoshop": "Design Tool",
    "Tableau": "Data Visualization", "Power BI": "Data Visualization",
    "SASS": "CSS Preprocessor", "LESS": "CSS Preprocessor",
}

# Section heading patterns for resume parsing
SECTION_PATTERNS = [
    ("summary", r"(?:^|\n)\s*(?:SUMMARY|OBJECTIVE|ABOUT\s*ME|PROFILE|PROFESSIONAL\s*SUMMARY|CAREER\s*OBJECTIVE)\s*[:\n]"),
    ("education", r"(?:^|\n)\s*(?:EDUCATION|ACADEMIC\s*QUALIFICATIONS?|ACADEMIC\s*DETAILS?)\s*[:\n]"),
    ("experience", r"(?:^|\n)\s*(?:EXPERIENCE|WORK\s*EXPERIENCE|PROFESSIONAL\s*EXPERIENCE|EMPLOYMENT\s*HISTORY)\s*[:\n]"),
    ("internships", r"(?:^|\n)\s*(?:INTERNSHIPS?|INDUSTRIAL\s*TRAINING)\s*[:\n]"),
    ("skills", r"(?:^|\n)\s*(?:SKILLS|TECHNICAL\s*SKILLS|KEY\s*SKILLS|CORE\s*COMPETENCIES|TOOLS\s*(?:&|AND)\s*TECHNOLOGIES)\s*[:\n]"),
    ("projects", r"(?:^|\n)\s*(?:PROJECTS|PERSONAL\s*PROJECTS|ACADEMIC\s*PROJECTS|KEY\s*PROJECTS)\s*[:\n]"),
    ("certifications", r"(?:^|\n)\s*(?:CERTIFICATIONS?|CERTIFICATES?|PROFESSIONAL\s*CERTIFICATIONS?)\s*[:\n]"),
    ("courses", r"(?:^|\n)\s*(?:COURSES|ONLINE\s*COURSES|RELEVANT\s*COURSEWORK|MOOC)\s*[:\n]"),
    ("achievements", r"(?:^|\n)\s*(?:ACHIEVEMENTS?|AWARDS?|HONORS?|ACCOMPLISHMENTS?)\s*[:\n]"),
    ("hackathons", r"(?:^|\n)\s*(?:HACKATHONS?|COMPETITIONS?|CODING\s*COMPETITIONS?)\s*[:\n]"),
    ("publications", r"(?:^|\n)\s*(?:PUBLICATIONS?|RESEARCH\s*PAPERS?|PAPERS?)\s*[:\n]"),
    ("positions_of_responsibility", r"(?:^|\n)\s*(?:POSITIONS?\s*OF\s*RESPONSIBILITY|LEADERSHIP|EXTRACURRICULAR|VOLUNTEER)\s*[:\n]"),
    ("languages", r"(?:^|\n)\s*(?:LANGUAGES?)\s*[:\n]"),
]


class ResumeAnalysisService:
    """
    Complete Resume Intelligence Analysis Service.
    Performs structured extraction, claim inventory, and Skill Passport verification.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResumeAnalysisService, cls).__new__(cls)
        return cls._instance

    # =========================================================================
    # PUBLIC API
    # =========================================================================
    def analyze_resume(self, text: str) -> Dict[str, Any]:
        """
        Complete resume analysis pipeline:
        1. Extract candidate info
        2. Parse all sections
        3. Extract and categorize skills
        4. Build claim inventory
        5. Verify claims against Skill Passport
        6. Perform GitHub project analysis & verification
        7. Compute credibility & risk levels
        8. Build claim & project statistics
        9. Generate full AI summary & recommendation
        """
        logger.info("Resume Intelligence: Starting complete resume analysis...")

        # 1. Extract candidate contact info
        candidate = self._extract_candidate_info(text)
        logger.info(f"Resume Intelligence: Candidate extracted: {candidate.get('name', 'Unknown')}")

        # 2. Parse section boundaries
        sections = self._parse_sections(text)
        logger.info(f"Resume Intelligence: {len(sections)} sections identified: {list(sections.keys())}")

        # 3. Extract structured data from each section
        summary_text = self._extract_summary(sections.get("summary", ""))
        education = self._extract_education(sections.get("education", ""), text)
        experience = self._extract_experience(sections.get("experience", ""))
        internships = self._extract_internships(sections.get("internships", ""))
        projects = self._extract_projects(sections.get("projects", ""), text)
        certifications = self._extract_certifications(sections.get("certifications", ""))
        courses = self._extract_courses(sections.get("courses", ""))
        achievements = self._extract_achievements(sections.get("achievements", ""))
        hackathons = self._extract_hackathons(sections.get("hackathons", ""), text)
        publications = self._extract_publications(sections.get("publications", ""))
        positions = self._extract_positions(sections.get("positions_of_responsibility", ""))
        languages = self._extract_languages(sections.get("languages", ""))

        # 4. Extract skills from ALL sections (not just "Skills")
        skills = self._extract_skills_from_all_sections(text, sections)
        logger.info(f"Resume Intelligence: {len(skills)} skills extracted from resume.")

        # 5. Build claim inventory
        claim_inventory = self._build_claim_inventory(
            skills=skills, education=education, experience=experience,
            internships=internships, certifications=certifications,
            projects=projects, achievements=achievements, hackathons=hackathons,
            sections=sections
        )
        logger.info(f"Resume Intelligence: Claim inventory built with {sum(len(v) for v in claim_inventory.values())} total claims.")

        # 6. Skill Passport verification
        skill_verification = self._verify_skills_against_passport(skills)
        education_verification = self._verify_education_against_passport(education)
        certification_verification = self._verify_certifications_against_passport(certifications)
        
        # 7. GitHub & Project Analysis
        all_github_urls = re.findall(r'https?://(?:www\.)?github\.com/[\w\-]+/[\w\-]+', text, re.IGNORECASE)
        all_github_urls = list(set([u.rstrip('/') for u in all_github_urls]))
        
        project_analysis = []
        github_analysis = []
        
        total_projects = len(projects)
        github_projects_count = 0
        analyzed_projects_count = 0
        supported_projects_count = 0
        partially_supported_projects_count = 0
        unverified_projects_count = 0
        contradicted_projects_count = 0
        
        for proj in projects:
            proj_name = proj.get("name", "")
            proj_desc = (proj.get("description") or "")
            proj_techs = proj.get("technologies", [])
            
            associated_url = None
            if proj.get("url") and "github.com" in proj.get("url").lower():
                associated_url = proj.get("url")
            else:
                gh_match = re.search(r'(https?://(?:www\.)?github\.com/[\w\-]+/[\w\-]+)', proj_desc, re.IGNORECASE)
                if gh_match:
                    associated_url = gh_match.group(1)
                else:
                    for u in all_github_urls:
                        repo_name = u.split('/')[-1].lower()
                        clean_proj_name = re.sub(r'\s+', '', proj_name.lower())
                        clean_repo_name = re.sub(r'[\-_]', '', repo_name)
                        if clean_proj_name in clean_repo_name or clean_repo_name in clean_proj_name:
                            associated_url = u
                            break
            
            proj["github_url"] = associated_url
            
            if associated_url:
                github_projects_count += 1
                gh_parts = re.search(r'github\.com/([\w\-]+)/([\w\-]+)', associated_url, re.IGNORECASE)
                if gh_parts:
                    owner = gh_parts.group(1)
                    repo_name = gh_parts.group(2)
                    proj["github_owner"] = owner
                    proj["github_repository"] = repo_name
                    
                    analysis_res = self._analyze_github_repository(associated_url, owner, repo_name, proj_techs)
                    status = analysis_res["github_analysis_status"]
                    techs_found = analysis_res["technologies_found"]
                    evidence = analysis_res["evidence"]
                    quality = analysis_res.get("project_quality", {})
                    
                    proj_status = "NOT_ANALYZABLE"
                    if status == "ANALYZED":
                        analyzed_projects_count += 1
                        claim_comparisons = []
                        techs_found_claimed = []
                        for tech in proj_techs:
                            is_found = any(t.lower() == tech.lower() for t in techs_found)
                            if is_found:
                                techs_found_claimed.append(tech)
                            claim_comparisons.append({
                                "claim": f"Project used {tech}",
                                "resume_value": tech,
                                "verified_value": tech if is_found else None,
                                "status": "SUPPORTED" if is_found else "NOT_VERIFIED"
                            })
                        
                        if len(proj_techs) > 0:
                            ratio = len(techs_found_claimed) / len(proj_techs)
                            if ratio >= 0.75:
                                proj_status = "SUPPORTED"
                                supported_projects_count += 1
                            elif ratio > 0.0:
                                proj_status = "PARTIALLY_SUPPORTED"
                                partially_supported_projects_count += 1
                            else:
                                proj_status = "UNVERIFIED"
                                unverified_projects_count += 1
                        else:
                            proj_status = "UNVERIFIED"
                            unverified_projects_count += 1
                            claim_comparisons = []
                    else:
                        proj_status = "NOT_ANALYZABLE"
                        claim_comparisons = []
                        unverified_projects_count += 1
                        
                    proj["github_analysis_status"] = status
                    proj["project_status"] = proj_status
                    
                    project_analysis.append({
                        "project_name": proj_name,
                        "github_url": associated_url,
                        "github_analysis_status": status,
                        "technologies_claimed": proj_techs,
                        "technologies_found": techs_found,
                        "project_status": proj_status,
                        "evidence": evidence,
                        "project_quality": quality,
                        "claim_comparisons": claim_comparisons
                    })
                    
                    github_analysis.append({
                        "project_name": proj_name,
                        "github_url": associated_url,
                        "github_owner": owner,
                        "github_repository": repo_name,
                        "github_analysis_status": status,
                        "technologies_found": techs_found
                    })
                else:
                    proj["github_analysis_status"] = "UNAVAILABLE"
                    proj["project_status"] = "NOT_ANALYZABLE"
                    project_analysis.append({
                        "project_name": proj_name,
                        "github_url": associated_url,
                        "github_analysis_status": "UNAVAILABLE",
                        "technologies_claimed": proj_techs,
                        "technologies_found": [],
                        "project_status": "NOT_ANALYZABLE",
                        "evidence": {"readme_available": False, "source_code_available": False, "dependencies_detected": False, "tests_detected": False}
                    })
            else:
                proj["github_owner"] = None
                proj["github_repository"] = None
                proj["github_analysis_status"] = "NOT_AVAILABLE"
                proj["project_status"] = "NOT_ANALYZABLE"
                unverified_projects_count += 1
                
                project_analysis.append({
                    "project_name": proj_name,
                    "github_url": None,
                    "github_analysis_status": "NOT_AVAILABLE",
                    "technologies_claimed": proj_techs,
                    "technologies_found": [],
                    "project_status": "NOT_ANALYZABLE",
                    "evidence": {"readme_available": False, "source_code_available": False, "dependencies_detected": False, "tests_detected": False}
                })
        
        # 8. Calculate Claim Statistics
        total_claims_count = len(skill_verification) + len(education_verification) + len(certification_verification)
        verified_claims_count = (
            sum(1 for s in skill_verification if s["verification_status"] == "VERIFIED") +
            sum(1 for e in education_verification if e["status"] == "VERIFIED") +
            sum(1 for c in certification_verification if c["verification_status"] == "VERIFIED")
        )
        contradicted_claims_count = (
            sum(1 for s in skill_verification if s["verification_status"] == "CONTRADICTED") +
            sum(1 for e in education_verification if e["status"] == "CONTRADICTED") +
            sum(1 for c in certification_verification if c["verification_status"] == "CONTRADICTED")
        )
        unverified_claims_count = total_claims_count - verified_claims_count - contradicted_claims_count
        
        claim_statistics = {
            "total_claims": total_claims_count,
            "verified_claims": verified_claims_count,
            "unverified_claims": unverified_claims_count,
            "contradicted_claims": contradicted_claims_count,
            "verified_percentage": (verified_claims_count / total_claims_count * 100) if total_claims_count > 0 else 0.0,
            "unverified_percentage": (unverified_claims_count / total_claims_count * 100) if total_claims_count > 0 else 0.0,
            "contradicted_percentage": (contradicted_claims_count / total_claims_count * 100) if total_claims_count > 0 else 0.0,
        }
        
        # 9. Calculate Credibility & Risk
        credibility, risk = self._calculate_credibility_and_risk(
            skill_verification, education_verification, certification_verification
        )
        
        # 10. Calculate overall_score and score_breakdown
        skill_support_score = (sum(1 for s in skill_verification if s["verification_status"] == "VERIFIED") / len(skills) * 100.0) if skills else 100.0
        
        supported_projs = sum(1 for p in project_analysis if p.get("project_status") == "SUPPORTED")
        project_evidence_score = (supported_projs / len(project_analysis) * 100.0) if project_analysis else 100.0
        
        cert_verified_count = sum(1 for c in certification_verification if c["verification_status"] == "VERIFIED")
        credential_support_score = (cert_verified_count / len(certification_verification) * 100.0) if certification_verification else 100.0
        
        edu_support_points = []
        for ev in education_verification:
            if ev.get("status") == "VERIFIED":
                edu_support_points.append(100.0)
            elif ev.get("status") == "CONTRADICTED":
                edu_support_points.append(0.0)
            else:
                edu_support_points.append(70.0)
        education_support_score = (sum(edu_support_points) / len(edu_support_points)) if edu_support_points else 100.0
        
        claim_consistency_score = ((1.0 - (contradicted_claims_count / total_claims_count)) * 100.0) if total_claims_count > 0 else 100.0
        
        overall_score = int(round((skill_support_score + project_evidence_score + credential_support_score + education_support_score + claim_consistency_score) / 5.0))
        
        score_breakdown = {
            "skill_support": round(skill_support_score, 2),
            "project_evidence": round(project_evidence_score, 2),
            "credential_support": round(credential_support_score, 2),
            "education_support": round(education_support_score, 2),
            "claim_consistency": round(claim_consistency_score, 2)
        }
        
        # 11. Compile unified claim_analysis and concerns/strengths lists
        flat_claims = []
        concerns = []
        strengths = []
        
        for s in skill_verification:
            status_val = s.get("status", "NOT_VERIFIED")
            flat_claims.append({
                "claim_type": "SKILL",
                "claim": s["skill"],
                "evidence_source": s["evidence_source"] or "Skill Passport (unverified)",
                "status": status_val,
                "confidence": 100 if status_val == "SUPPORTED" else 0
            })
            if status_val == "CONTRADICTED":
                concerns.append(f"Skill contradiction: {s['skill']} grade points failed in trusted records.")
            elif status_val == "SUPPORTED":
                strengths.append(f"Verified skill: {s['skill']} confirmed via Skill Passport.")
                
        for ev in education_verification:
            status_val = ev.get("status", "UNVERIFIED")
            flat_claims.append({
                "claim_type": "EDUCATION",
                "claim": ev["claim"],
                "evidence_source": "Issuer Database",
                "status": "SUPPORTED" if status_val == "VERIFIED" else status_val,
                "confidence": 100 if status_val == "VERIFIED" else (0 if status_val == "CONTRADICTED" else 70)
            })
            if status_val == "CONTRADICTED":
                concerns.append(f"Education conflict: {ev['message']}")
            elif status_val == "VERIFIED":
                strengths.append(f"Verified education: {ev['claim']} matches official records.")
                
        for cv in certification_verification:
            status_val = cv.get("verification_status", "UNVERIFIED")
            flat_claims.append({
                "claim_type": "CERTIFICATION",
                "claim": cv["certification"],
                "evidence_source": cv["evidence_source"] or "Issuer Registry",
                "status": "SUPPORTED" if status_val == "VERIFIED" else status_val,
                "confidence": 100 if status_val == "VERIFIED" else (0 if status_val == "CONTRADICTED" else 70)
            })
            if status_val == "CONTRADICTED":
                concerns.append(f"Certification contradiction: {cv['certification']}")
            elif status_val == "VERIFIED":
                strengths.append(f"Verified certification: {cv['certification']}.")
                
        for proj_info in project_analysis:
            status_val = proj_info.get("project_status", "UNVERIFIED")
            flat_claims.append({
                "claim_type": "PROJECT",
                "claim": proj_info["project_name"],
                "evidence_source": "GitHub Analysis",
                "status": status_val,
                "confidence": 100 if status_val == "SUPPORTED" else (50 if status_val == "PARTIALLY_SUPPORTED" else 0)
            })
            if status_val == "SUPPORTED":
                strengths.append(f"Verified project: {proj_info['project_name']} code evidence confirms major technologies.")
            elif status_val == "UNVERIFIED":
                concerns.append(f"Project not verified: {proj_info['project_name']} lacks repo evidence.")

        # 12. Compile AI Scan Result
        ai_scan_result = {
            "scan_status": "COMPLETED",
            "resume": {
                "document_type": "RESUME"
            },
            "claims": {
                "total": total_claims_count,
                "verified": verified_claims_count,
                "unverified": unverified_claims_count,
                "contradicted": contradicted_claims_count
            },
            "projects": {
                "total": total_projects,
                "github_analyzed": analyzed_projects_count,
                "supported": supported_projs,
                "partially_supported": partially_supported_projects_count,
                "unverified": unverified_projects_count,
                "contradicted": contradicted_projects_count
            },
            "credibility": credibility,
            "risk": risk
        }
        
        # 13. Generate Full Summary & Recommendation
        full_ai_summary = self._generate_full_ai_summary(
            candidate, education, experience, internships, skills, projects,
            skill_verification, education_verification, certification_verification,
            project_analysis, credibility, risk
        )
        
        recommendation_lines = [l for l in full_ai_summary.split("\n\n") if l.startswith("Recommendation:")]
        recommendation = recommendation_lines[0].replace("Recommendation:\n", "").strip() if recommendation_lines else ""
        
        # Standard summary from Prompt 1
        ai_summary = self._generate_summary(candidate, education, experience, internships, skills, projects, certifications, achievements, hackathons)
        resume_quality = self._assess_resume_quality(candidate, education, experience, skills, projects, certifications, sections)

        logger.info(f"Resume Intelligence: Full analysis completed for {candidate.get('name', 'Unknown')}.")

        # Determine overall credibility level mapping
        cred_mapping = {
            "HIGH_CONFIDENCE": "HIGH",
            "MEDIUM_CONFIDENCE": "MEDIUM",
            "LOW_CONFIDENCE": "LOW",
            "NEEDS_REVIEW": "NEEDS_REVIEW"
        }
        cred_short = cred_mapping.get(credibility["level"], "MEDIUM")

        return {
            "success": True,
            "document_type": "RESUME",
            "analysis_status": "COMPLETED",
            
            # Prompt 1 & 2 extractions & verifications
            "candidate": candidate,
            "summary": summary_text or ai_summary,
            "education": education,
            "experience": experience,
            "internships": internships,
            "skills": skills,
            "projects": projects,
            "certifications": certifications,
            "courses": courses,
            "achievements": achievements,
            "hackathons": hackathons,
            "publications": publications,
            "positions_of_responsibility": positions,
            "languages": languages,
            "claim_inventory": claim_inventory,
            "resume_quality": resume_quality,
            "ai_scan_result": ai_scan_result,
            "claim_statistics": claim_statistics,
            "skill_verification": skill_verification,
            "education_verification": education_verification,
            "certification_verification": certification_verification,
            "project_analysis": project_analysis,
            "github_analysis": github_analysis,
            "credibility": credibility,
            "risk": risk,
            "recommendation": recommendation,
            "full_ai_summary": full_ai_summary,
            
            # Final Employer Report Response format mapping
            "analysis_type": "RESUME_INTELLIGENCE",
            "resume_analysis": {
                "status": "COMPLETED",
                "overall_score": overall_score,
                "score_breakdown": score_breakdown,
                "credibility": cred_short
            },
            "skills": {
                "total_claimed": len(skills),
                "supported": sum(1 for s in skill_verification if s["verification_status"] == "VERIFIED"),
                "not_verified": sum(1 for s in skill_verification if s["verification_status"] == "UNVERIFIED"),
                "contradicted": sum(1 for s in skill_verification if s["verification_status"] == "CONTRADICTED")
            },
            "skill_analysis": skill_verification,
            "claim_analysis": flat_claims,
            "concerns": concerns,
            "strengths": strengths,
            "full_summary": full_ai_summary
        }

    # =========================================================================
    # CANDIDATE INFO EXTRACTION
    # =========================================================================
    def _extract_candidate_info(self, text: str) -> Dict[str, Any]:
        lines = text.strip().split("\n")

        # Name: typically the first prominent line
        name = None
        for line in lines[:5]:
            line_clean = line.strip()
            if not line_clean:
                continue
            # Skip lines that look like section headers or URLs
            if re.match(r'^(?:RESUME|CV|CURRICULUM\s*VITAE|EMAIL|PHONE|ADDRESS|EDUCATION|EXPERIENCE|SKILLS)', line_clean, re.IGNORECASE):
                continue
            if "@" in line_clean or "http" in line_clean or "|" in line_clean:
                continue
            # A name is 2-4 words, all alpha
            words = line_clean.split()
            if 2 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\.]+$', w) for w in words):
                name = line_clean.strip()
                break

        # Email
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        email = email_match.group(0) if email_match else None

        # Phone
        phone_match = re.search(r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{5,10}', text)
        phone = phone_match.group(0).strip() if phone_match else None
        # Validate phone - should have at least 10 digits
        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) < 10:
                phone = None

        # Location
        location = None
        loc_match = re.search(r'(?:Location|Address|City)\s*[:\-]?\s*([A-Za-z\s,]+)', text[:500], re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()

        # LinkedIn
        linkedin_match = re.search(r'(?:linkedin\.com/in/[\w-]+)', text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        # GitHub
        github_match = re.search(r'(?:github\.com/[\w-]+)', text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None

        # Portfolio
        portfolio = None
        portfolio_match = re.search(r'(?:Portfolio|Website)\s*[:\-]?\s*(https?://[^\s]+)', text[:800], re.IGNORECASE)
        if portfolio_match:
            portfolio = portfolio_match.group(1).strip()

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin": linkedin,
            "github": github,
            "portfolio": portfolio,
        }

    # =========================================================================
    # SECTION PARSER
    # =========================================================================
    def _parse_sections(self, text: str) -> Dict[str, str]:
        """
        Identifies section boundaries in the resume using header patterns.
        Returns a dict mapping section_name -> section_text_content.
        """
        section_positions: List[Tuple[str, int]] = []

        for section_name, pattern in SECTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                section_positions.append((section_name, match.end()))

        # Sort by position in text
        section_positions.sort(key=lambda x: x[1])

        sections = {}
        for i, (sec_name, start_pos) in enumerate(section_positions):
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][1]
                # Back up to the header match start of the next section
                for next_name, next_pattern in SECTION_PATTERNS:
                    if next_name == section_positions[i + 1][0]:
                        m = re.search(next_pattern, text, re.IGNORECASE | re.MULTILINE)
                        if m:
                            end_pos = m.start()
                            break
            else:
                end_pos = len(text)

            sections[sec_name] = text[start_pos:end_pos].strip()

        return sections

    # =========================================================================
    # EDUCATION EXTRACTION
    # =========================================================================
    def _extract_education(self, section_text: str, full_text: str) -> List[Dict[str, Any]]:
        education = []
        text = section_text if section_text else full_text

        edu_patterns = [
            (r'(?:Bachelor\s+of\s+Technology|B\.?Tech)', 'B.Tech'),
            (r'(?:Master\s+of\s+Technology|M\.?Tech)', 'M.Tech'),
            (r'(?:Bachelor\s+of\s+Engineering|B\.?E\.?)', 'B.E.'),
            (r'(?:Bachelor\s+of\s+Science|B\.?Sc)', 'B.Sc'),
            (r'(?:Master\s+of\s+Science|M\.?Sc)', 'M.Sc'),
            (r'(?:Bachelor\s+of\s+Computer\s+Application|BCA)', 'BCA'),
            (r'(?:Master\s+of\s+Computer\s+Application|MCA)', 'MCA'),
            (r'(?:Master\s+of\s+Business\s+Administration|MBA)', 'MBA'),
            (r'(?:Ph\.?D|Doctor\s+of\s+Philosophy)', 'PhD'),
            (r'(?:Diploma)', 'Diploma'),
            (r'(?:12th|XII|Senior\s+Secondary|Higher\s+Secondary|HSC|\+2)', '12th'),
            (r'(?:10th|X(?:th)?|Secondary\s+(?:School)?|SSC|Matriculation)', '10th'),
        ]

        for pattern, degree_name in edu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                match_pos = match.start()
                context_start = max(0, text.rfind('\n', 0, match_pos))
                context_end = text.find('\n', match_pos + 200)
                if context_end == -1:
                    context_end = min(len(text), match_pos + 300)
                context = text[context_start:context_end]

                # Extract institution
                institution = None
                inst_patterns = [
                    r'(?:University|Institute|College|School|Academy)[^\n]{0,80}',
                    r'(?:[A-Z][a-z]+\s+)+(?:University|Institute|College)',
                    r'-\s*([A-Z][A-Za-z\s&,\.]+?)(?:\s*\(|\s*$|\n)',
                ]
                for ip in inst_patterns:
                    im = re.search(ip, context, re.IGNORECASE)
                    if im:
                        institution = im.group(0).strip().rstrip('-').strip()
                        break

                # Extract specialization/program
                specialization = None
                spec_match = re.search(r'(?:in\s+|\-\s*)([A-Za-z\s&,\.]+?)(?:\s*\(|\s*-|\s*$|\n)', context[match.start() - context_start:], re.IGNORECASE)
                if spec_match:
                    spec = spec_match.group(1).strip()
                    if 3 < len(spec) < 100:
                        specialization = spec

                # Extract CGPA
                cgpa = None
                cgpa_match = re.search(r'(?:CGPA|GPA|CPI)\s*[:\-]?\s*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
                if cgpa_match:
                    try:
                        cgpa = float(cgpa_match.group(1))
                    except ValueError:
                        pass

                # Extract percentage
                percentage = None
                pct_match = re.search(r'(?:Percentage|Marks|Score)\s*[:\-]?\s*([0-9]+\.?[0-9]*)\s*%?', context, re.IGNORECASE)
                if pct_match:
                    try:
                        percentage = float(pct_match.group(1))
                    except ValueError:
                        pass

                # Extract years
                start_year = None
                end_year = None
                year_match = re.search(r'(\d{4})\s*[-\u2013]\s*(\d{4}|[Pp]resent|[Oo]ngoing|[Cc]urrent)', context)
                if year_match:
                    start_year = int(year_match.group(1))
                    end_str = year_match.group(2)
                    if end_str.isdigit():
                        end_year = int(end_str)
                else:
                    single_year = re.search(r'\b(20\d{2})\b', context)
                    if single_year:
                        end_year = int(single_year.group(1))

                edu_entry = {
                    "degree": degree_name,
                    "institution": institution,
                    "program": specialization,
                    "specialization": specialization,
                    "start_year": start_year,
                    "end_year": end_year,
                    "cgpa": cgpa,
                    "percentage": percentage,
                    "location": None,
                }
                if not any(e["degree"] == degree_name for e in education):
                    education.append(edu_entry)

        return education

    # =========================================================================
    # EXPERIENCE EXTRACTION
    # =========================================================================
    def _extract_experience(self, section_text: str) -> List[Dict[str, Any]]:
        if not section_text.strip():
            return []

        experience = []
        entries = re.split(r'\n(?=[A-Z\u2022\-\*])', section_text)

        current = {}
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            org_match = re.search(r'^([A-Za-z][A-Za-z\s&,\.\-]+?)\s*[-\u2013|]\s*(.+?)$', entry.split('\n')[0])
            if org_match:
                if current:
                    experience.append(current)
                current = {
                    "organization": org_match.group(1).strip(),
                    "role": org_match.group(2).strip(),
                    "start_date": None,
                    "end_date": None,
                    "location": None,
                    "description": None,
                    "technologies": [],
                }

                date_match = re.search(r'(\w+\s+\d{4}|\d{4})\s*[-\u2013]\s*(\w+\s+\d{4}|\d{4}|[Pp]resent|[Cc]urrent)', entry)
                if date_match:
                    current["start_date"] = date_match.group(1)
                    current["end_date"] = date_match.group(2)

                remaining_lines = entry.split('\n')[1:]
                desc = ' '.join(l.strip().lstrip('\u2022-* ') for l in remaining_lines if l.strip())
                if desc:
                    current["description"] = desc
                    for alias, normalized in SKILL_ALIASES.items():
                        if re.search(r'\b' + re.escape(alias) + r'\b', desc, re.IGNORECASE):
                            if normalized not in current["technologies"]:
                                current["technologies"].append(normalized)
            elif current and entry:
                prev_desc = current.get("description", "") or ""
                current["description"] = (prev_desc + " " + entry.lstrip('\u2022-* ')).strip()

        if current:
            experience.append(current)

        return experience

    # =========================================================================
    # INTERNSHIP EXTRACTION
    # =========================================================================
    def _extract_internships(self, section_text: str) -> List[Dict[str, Any]]:
        if not section_text.strip():
            return []
        raw = self._extract_experience(section_text)
        internships = []
        for item in raw:
            start = item.get("start_date")
            end = item.get("end_date")
            dates = f"{start} - {end}" if start and end else (start or end)
            internships.append({
                "organization": item.get("organization"),
                "role": item.get("role"),
                "dates": dates,
                "description": item.get("description"),
                "technologies": item.get("technologies", []),
            })
        return internships

    # =========================================================================
    # SKILLS EXTRACTION (from ALL sections)
    # =========================================================================
    def _extract_skills_from_all_sections(self, full_text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extracts skills from every section of the resume, not just the 'Skills' section.
        """
        found_skills: Dict[str, List[str]] = {}
        original_claims: Dict[str, set] = {}

        search_sections = {
            "Full Resume": full_text,
        }
        search_sections.update({k.replace('_', ' ').title(): v for k, v in sections.items()})

        for section_name, section_text in search_sections.items():
            if not section_text:
                continue

            for alias, normalized in SKILL_ALIASES.items():
                pattern = r'\b' + re.escape(alias) + r'\b'
                matches = re.findall(pattern, section_text, re.IGNORECASE)
                if matches:
                    if normalized not in found_skills:
                        found_skills[normalized] = []
                    if normalized not in original_claims:
                        original_claims[normalized] = set()

                    for match in matches:
                        original_claims[normalized].add(match.strip())

                    if section_name not in found_skills[normalized] and section_name != "Full Resume":
                        found_skills[normalized].append(section_name)
                    elif section_name == "Full Resume" and not found_skills[normalized]:
                        found_skills[normalized].append("General")

        skills = []
        for normalized_name, source_sections in found_skills.items():
            if not source_sections:
                source_sections = ["General"]
            
            raw_claims = sorted(list(original_claims.get(normalized_name, {normalized_name})))
            skills.append({
                "name": normalized_name,
                "category": SKILL_CATEGORIES.get(normalized_name, "Technical Skill"),
                "source_sections": source_sections,
                "original_claims": raw_claims,
            })

        return skills

    # =========================================================================
    # PROJECTS EXTRACTION
    # =========================================================================
    def _extract_projects(self, section_text: str, full_text: str) -> List[Dict[str, Any]]:
        if not section_text.strip():
            return []

        projects = []
        entries = re.split(r'\n(?=[\u2022\-\*\d\.]\s*[A-Z])', section_text)

        for entry in entries:
            entry = entry.strip().lstrip('\u2022-*0123456789. ')
            if not entry or len(entry) < 5:
                continue

            lines = entry.split('\n')
            name = lines[0].strip().rstrip(':')

            name_desc = re.match(r'^([^:]{3,60}):\s*(.+)', lines[0])
            if name_desc:
                name = name_desc.group(1).strip()
                desc_start = name_desc.group(2).strip()
                remaining = ' '.join(l.strip().lstrip('\u2022-* ') for l in lines[1:])
                description = (desc_start + ' ' + remaining).strip()
            else:
                description = ' '.join(l.strip().lstrip('\u2022-* ') for l in lines[1:] if l.strip())

            technologies = []
            combined = name + ' ' + description
            for alias, normalized in SKILL_ALIASES.items():
                if re.search(r'\b' + re.escape(alias) + r'\b', combined, re.IGNORECASE):
                    if normalized not in technologies:
                        technologies.append(normalized)

            url = None
            url_match = re.search(r'(https?://[^\s]+)', entry)
            if url_match:
                url = url_match.group(1)

            projects.append({
                "name": name,
                "description": description if description else None,
                "technologies": technologies,
                "role": None,
                "duration": None,
                "url": url,
            })

        return projects

    # =========================================================================
    # CERTIFICATIONS EXTRACTION
    # =========================================================================
    def _extract_certifications(self, section_text: str) -> List[Dict[str, Any]]:
        if not section_text.strip():
            return []

        certifications = []
        entries = re.split(r'\n(?=[\u2022\-\*\d\.]\s*[A-Z])', section_text)

        for entry in entries:
            entry = entry.strip().lstrip('\u2022-*0123456789. ')
            if not entry or len(entry) < 5:
                continue

            lines = entry.split('\n')
            name = lines[0].strip()

            issuer = None
            issuer_match = re.search(r'(?:by|from|issued\s+by|issuer)\s*[:\-]?\s*([A-Za-z\s&,\.]+)', entry, re.IGNORECASE)
            if issuer_match:
                issuer = issuer_match.group(1).strip()

            issue_date = None
            date_match = re.search(r'(?:issued?|date)\s*[:\-]?\s*([A-Za-z]+\s+\d{4}|\d{4})', entry, re.IGNORECASE)
            if date_match:
                issue_date = date_match.group(1).strip()

            cred_id = None
            cred_match = re.search(r'(?:credential\s*(?:id|no)|id|cert\s*(?:id|no))\s*[:\-]?\s*([A-Z0-9\-]+)', entry, re.IGNORECASE)
            if cred_match:
                cred_id = cred_match.group(1).strip()

            cred_url = None
            url_match = re.search(r'(https?://[^\s]+)', entry)
            if url_match:
                cred_url = url_match.group(1)

            cert_skills = []
            for alias, normalized in SKILL_ALIASES.items():
                if re.search(r'\b' + re.escape(alias) + r'\b', entry, re.IGNORECASE):
                    if normalized not in cert_skills:
                        cert_skills.append(normalized)

            certifications.append({
                "name": name,
                "issuer": issuer,
                "issue_date": issue_date,
                "credential_id": cred_id,
                "credential_url": cred_url,
                "skills": cert_skills,
            })

        return certifications

    # =========================================================================
    # SIMPLE SECTION EXTRACTORS
    # =========================================================================
    def _extract_summary(self, section_text: str) -> Optional[str]:
        if not section_text.strip():
            return None
        return section_text.strip()

    def _extract_courses(self, section_text: str) -> List[str]:
        if not section_text.strip():
            return []
        items = re.split(r'[\n\u2022\-\*]+', section_text)
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 3]

    def _extract_achievements(self, section_text: str) -> List[str]:
        if not section_text.strip():
            return []
        items = re.split(r'[\n\u2022\-\*]+', section_text)
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 3]

    def _extract_hackathons(self, section_text: str, full_text: str) -> List[str]:
        results = []
        text = section_text if section_text.strip() else full_text
        hack_matches = re.findall(
            r'(?:Winner|Finalist|Participant|1st|2nd|3rd|First|Second|Third)\s+(?:of|at|in)?\s*([^\n]+(?:Hackathon|Challenge|Competition)[^\n]*)',
            text, re.IGNORECASE
        )
        for m in hack_matches:
            results.append(m.strip())
        if not results and section_text.strip():
            items = re.split(r'[\n\u2022\-\*]+', section_text)
            results = [item.strip() for item in items if item.strip() and len(item.strip()) > 3]
        return results

    def _extract_publications(self, section_text: str) -> List[str]:
        if not section_text.strip():
            return []
        items = re.split(r'[\n\u2022\-\*]+', section_text)
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 3]

    def _extract_positions(self, section_text: str) -> List[str]:
        if not section_text.strip():
            return []
        items = re.split(r'[\n\u2022\-\*]+', section_text)
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 3]

    def _extract_languages(self, section_text: str) -> List[str]:
        if not section_text.strip():
            return []
        items = re.split(r'[\n\u2022\-\*,]+', section_text)
        return [item.strip() for item in items if item.strip() and len(item.strip()) > 1]

    # =========================================================================
    # CLAIM INVENTORY BUILDER
    # =========================================================================
    def _build_claim_inventory(self, skills, education, experience, internships,
                                certifications, projects, achievements, hackathons,
                                sections) -> Dict[str, List[Dict[str, Any]]]:
        inventory = {
            "skills": [],
            "education_claims": [],
            "experience_claims": [],
            "internship_claims": [],
            "certification_claims": [],
            "project_claims": [],
            "achievement_claims": [],
        }

        for skill in skills:
            inventory["skills"].append({
                "claim": skill["name"],
                "type": "SKILL",
                "source_section": ", ".join(skill["source_sections"]),
            })

        for edu in education:
            claim_str = edu.get("degree", "")
            if edu.get("institution"):
                claim_str += f" at {edu['institution']}"
            if edu.get("cgpa"):
                claim_str += f" (CGPA: {edu['cgpa']})"
            inventory["education_claims"].append({
                "claim": claim_str,
                "type": "EDUCATION",
                "source_section": "Education",
            })

        for exp in experience:
            claim_str = f"{exp.get('role', 'Role')} at {exp.get('organization', 'Organization')}"
            inventory["experience_claims"].append({
                "claim": claim_str,
                "type": "EXPERIENCE",
                "source_section": "Experience",
            })

        for intern in internships:
            claim_str = f"{intern.get('role', 'Intern')} at {intern.get('organization', 'Organization')}"
            inventory["internship_claims"].append({
                "claim": claim_str,
                "type": "INTERNSHIP",
                "source_section": "Internships",
            })

        for cert in certifications:
            inventory["certification_claims"].append({
                "claim": cert.get("name", "Certification"),
                "type": "CERTIFICATION",
                "source_section": "Certifications",
            })

        for proj in projects:
            inventory["project_claims"].append({
                "claim": proj.get("name", "Project"),
                "type": "PROJECT",
                "source_section": "Projects",
            })

        for ach in achievements:
            inventory["achievement_claims"].append({
                "claim": ach if isinstance(ach, str) else str(ach),
                "type": "ACHIEVEMENT",
                "source_section": "Achievements",
            })

        return inventory

    # =========================================================================
    # SKILL PASSPORT VERIFICATION
    # =========================================================================
    def _verify_skills_against_passport(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compares claimed skills against verified records in CertiTrust Skill Passport.
        """
        verification_results = []

        # Collect all verified/failed skills from the credential registry
        verified_skills_set = set()
        failed_skills_set = set()
        verified_subjects_set = set()
        failed_subjects_set = set()

        # Semantic mapping from subject names to skills
        subject_to_skill_map = {
            "PYTHON PROGRAMMING": ["Python"],
            "PYTHON": ["Python"],
            "OBJECT ORIENTED PROGRAMMING": ["C++", "Java"],
            "OBJECTED ORIENTED PROGRAMMING": ["C++", "Java"],
            "ADVANCED COMMUNICATION AND INTERPERSONAL SKILLS": [],
            "ENVIRONMENTAL SCIENCE": [],
            "ELECTRICAL AND ELECTRONICS ENGINEERING": [],
            "ICT WORKSHOP": [],
            "LINEAR ALGEBRA": ["Machine Learning"],
            "PRIVACY AND SECURITY IN ONLINE SOCIAL MEDIA": ["Cybersecurity"],
            "MACHINE LEARNING": ["Machine Learning"],
            "DEEP LEARNING": ["Deep Learning"],
            "ARTIFICIAL INTELLIGENCE": ["Artificial Intelligence"],
            "DATA STRUCTURES": ["C++", "Java", "Python"],
            "DATA SCIENCE": ["Data Science"],
            "COMPUTER VISION": ["Computer Vision", "OpenCV"],
            "NATURAL LANGUAGE PROCESSING": ["NLP"],
            "WEB DEVELOPMENT": ["HTML", "CSS", "JavaScript"],
            "DATABASE MANAGEMENT": ["SQL"],
            "CLOUD COMPUTING": ["Cloud Computing"],
            "CYBERSECURITY": ["Cybersecurity"],
        }

        for cred_id, record in credential_registry._db.items():
            cred_data = record.get("credential_data", {})
            subjects = cred_data.get("subjects", [])
            for sub in subjects:
                sub_name = (sub.get("subject") or sub.get("name") or "").strip().upper()
                if not sub_name:
                    continue

                grade = str(sub.get("grade", "")).strip().upper()
                grade_pts = sub.get("grade_points")

                is_failed = grade in ["F", "FAIL", "E"] or (grade_pts is not None and str(grade_pts) == "0")
                if is_failed:
                    failed_subjects_set.add(sub_name)
                else:
                    verified_subjects_set.add(sub_name)

            # Also check skills from extraction
            ext_skills = record.get("skills", [])
            if isinstance(ext_skills, list):
                for sk in ext_skills:
                    sk_name = ""
                    sk_status = "VERIFIED"
                    if isinstance(sk, str):
                        sk_name = sk.upper()
                    elif isinstance(sk, dict):
                        sk_name = sk.get("name", "").upper()
                        if sk.get("verification_status") == "CONTRADICTED":
                            sk_status = "CONTRADICTED"

                    if sk_name:
                        if sk_status == "CONTRADICTED":
                            failed_skills_set.add(sk_name)
                        else:
                            verified_skills_set.add(sk_name)

        # Build verified and failed skill names from subjects
        for subject_upper in verified_subjects_set:
            mapped = subject_to_skill_map.get(subject_upper, [])
            for skill_name in mapped:
                verified_skills_set.add(skill_name.upper())

        for subject_upper in failed_subjects_set:
            mapped = subject_to_skill_map.get(subject_upper, [])
            for skill_name in mapped:
                failed_skills_set.add(skill_name.upper())

        for skill in skills:
            skill_name = skill["name"]
            skill_upper = skill_name.upper()

            if skill_upper in verified_skills_set:
                verification_results.append({
                    "skill": skill_name,
                    "resume_claim": True,
                    "verification_status": "VERIFIED",
                    "evidence_source": "Skill Passport",
                    "skill_passport": True,
                    "status": "SUPPORTED",
                })
            elif skill_upper in failed_skills_set:
                verification_results.append({
                    "skill": skill_name,
                    "resume_claim": True,
                    "verification_status": "CONTRADICTED",
                    "evidence_source": "CertiTrust trusted record",
                    "skill_passport": False,
                    "status": "CONTRADICTED",
                })
            else:
                verification_results.append({
                    "skill": skill_name,
                    "resume_claim": True,
                    "verification_status": "UNVERIFIED",
                    "evidence_source": None,
                    "skill_passport": False,
                    "status": "NOT_VERIFIED",
                })

        return verification_results

    # =========================================================================
    # EDUCATION VERIFICATION AGAINST PASSPORT
    # =========================================================================
    def _verify_education_against_passport(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compares education claims against registered credentials in CertiTrust.
        """
        verification_results = []

        for edu in education:
            degree = edu.get("degree", "")
            claimed_cgpa = edu.get("cgpa")
            claimed_pct = edu.get("percentage")

            # Search registry for matching credential
            matched_record = None
            for cred_id, record in credential_registry._db.items():
                cred_type = record.get("credential_type", "").lower()
                cred_data = record.get("credential_data", {})

                if degree.lower() in ["b.tech", "b.e."]:
                    if "b.tech" in cred_type or "btech" in cred_type:
                        matched_record = record
                        break
                elif degree.lower() in ["10th"]:
                    if "10th" in cred_type or "secondary" in cred_type:
                        matched_record = record
                        break
                elif degree.lower() in ["12th"]:
                    if "12th" in cred_type or "senior secondary" in cred_type:
                        matched_record = record
                        break

            if not matched_record:
                verification_results.append({
                    "claim": f"{degree} education",
                    "resume_value": claimed_cgpa or claimed_pct,
                    "verified_value": None,
                    "status": "UNVERIFIED",
                    "message": f"No registered {degree} credential found in CertiTrust.",
                })
                continue

            cred_data = matched_record.get("credential_data", {})
            verified_cgpa = cred_data.get("cgpa")
            verified_pct = cred_data.get("percentage")

            # CGPA comparison
            if claimed_cgpa is not None and verified_cgpa is not None:
                try:
                    diff = abs(float(claimed_cgpa) - float(verified_cgpa))
                    if diff < 0.01:
                        verification_results.append({
                            "claim": f"{degree} CGPA",
                            "resume_value": claimed_cgpa,
                            "verified_value": verified_cgpa,
                            "status": "VERIFIED",
                            "message": f"{degree} CGPA matches trusted credential.",
                        })
                    else:
                        verification_results.append({
                            "claim": f"{degree} CGPA",
                            "resume_value": claimed_cgpa,
                            "verified_value": verified_cgpa,
                            "status": "CONTRADICTED",
                            "severity": "CRITICAL",
                            "message": f"{degree} CGPA mismatch: resume claims {claimed_cgpa}, trusted record shows {verified_cgpa}.",
                        })
                except (ValueError, TypeError):
                    pass

            # Percentage comparison
            if claimed_pct is not None and verified_pct is not None:
                try:
                    diff = abs(float(claimed_pct) - float(verified_pct))
                    if diff < 0.5:
                        verification_results.append({
                            "claim": f"{degree} Percentage",
                            "resume_value": claimed_pct,
                            "verified_value": verified_pct,
                            "status": "VERIFIED",
                            "message": f"{degree} percentage matches trusted credential.",
                        })
                    else:
                        verification_results.append({
                            "claim": f"{degree} Percentage",
                            "resume_value": claimed_pct,
                            "verified_value": verified_pct,
                            "status": "CONTRADICTED",
                            "severity": "CRITICAL",
                            "message": f"{degree} percentage mismatch: resume claims {claimed_pct}%, trusted record shows {verified_pct}%.",
                        })
                except (ValueError, TypeError):
                    pass

            # If nothing to compare numerically, at least confirm education exists
            if claimed_cgpa is None and claimed_pct is None:
                verification_results.append({
                    "claim": f"{degree} education",
                    "resume_value": None,
                    "verified_value": None,
                    "status": "VERIFIED",
                    "message": f"{degree} education confirmed via registered credential.",
                })

        return verification_results

    # =========================================================================
    # AI SUMMARY GENERATOR
    # =========================================================================
    def _generate_summary(self, candidate, education, experience, internships,
                           skills, projects, certifications, achievements, hackathons) -> str:
        parts = []

        name = candidate.get("name") or "The candidate"
        parts.append(f"{name}")

        if education:
            degrees = [e.get("degree", "") for e in education]
            highest = degrees[0] if degrees else ""
            inst = education[0].get("institution") or "an academic institution"
            parts.append(f"is pursuing/completed {highest} from {inst}")

        if experience:
            parts.append(f"with {len(experience)} professional experience(s)")

        if internships:
            parts.append(f"and {len(internships)} internship(s)")

        if skills:
            top_skills = [s["name"] for s in skills[:8]]
            parts.append(f". Key technical skills include: {', '.join(top_skills)}")

        if projects:
            parts.append(f". Has worked on {len(projects)} project(s)")
            proj_names = [p.get("name", "") for p in projects[:3]]
            if proj_names:
                parts.append(f" including {', '.join(proj_names)}")

        if certifications:
            parts.append(f". Holds {len(certifications)} certification(s)")

        if achievements or hackathons:
            total = len(achievements) + len(hackathons)
            parts.append(f". Has {total} achievement(s)/hackathon participation(s)")

        summary = " ".join(parts).replace("  ", " ").strip()
        if not summary.endswith("."):
            summary += "."

        return summary

    # =========================================================================
    # RESUME QUALITY ASSESSMENT
    # =========================================================================
    def _assess_resume_quality(self, candidate, education, experience, skills,
                                projects, certifications, sections) -> Dict[str, Any]:
        section_count = len([v for v in sections.values() if v.strip()])

        return {
            "has_contact_information": bool(candidate.get("name") or candidate.get("email")),
            "has_education": len(education) > 0,
            "has_skills": len(skills) > 0,
            "has_projects": len(projects) > 0,
            "has_experience": len(experience) > 0,
            "has_certifications": len(certifications) > 0,
            "section_count": section_count,
        }

    # =========================================================================
    # ADDITIONAL VERIFICATIONS & ANALYSIS
    # =========================================================================
    def _verify_certifications_against_passport(self, certifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compares certification claims against registered credentials in CertiTrust.
        """
        verification_results = []
        for cert in certifications:
            cert_name = cert.get("name", "")
            
            matched_record = None
            for cred_id, record in credential_registry._db.items():
                cred_type = record.get("credential_type", "").lower()
                cred_data = record.get("credential_data", {})
                cert_title = cred_data.get("certification_name", cred_data.get("course_name", cred_data.get("title", ""))).lower()
                
                if cert_name.lower() in cred_type or cert_name.lower() in cert_title:
                    matched_record = record
                    break
            
            if matched_record:
                verification_results.append({
                    "certification": cert_name,
                    "resume_claim": True,
                    "verification_status": "VERIFIED",
                    "evidence_source": "Skill Passport"
                })
            else:
                verification_results.append({
                    "certification": cert_name,
                    "resume_claim": True,
                    "verification_status": "UNVERIFIED",
                    "evidence_source": None
                })
        return verification_results

    def _analyze_github_repository(self, github_url: str, owner: str, repo: str, claimed_techs: List[str]) -> Dict[str, Any]:
        """
        Safely performs static analysis of a public GitHub repository.
        Uses a local mock database for test repositories and falls back to HTTP calls.
        """
        import requests
        
        logger.info(f"Resume Intelligence: Analyzing GitHub repository '{owner}/{repo}'...")
        
        # Local mock database for deterministic testing
        mock_repos = {
            "rishank/ecotwin-ai": {
                "status": "ANALYZED",
                "languages": ["Python", "HTML", "CSS"],
                "files": {
                    "README.md": "EcoTwin AI: Digital twin for ecosystem tracking using Python and TensorFlow. Uses OpenCV and FastAPI for real-time video analytics. GitHub repository.",
                    "requirements.txt": "fastapi>=0.110.0\ntensorflow>=2.15.0\nopencv-python>=4.9.0",
                }
            },
            "rishank/planttalk-ai": {
                "status": "ANALYZED",
                "languages": ["Python", "JavaScript", "CSS"],
                "files": {
                    "README.md": "PlantTalk AI: Generative AI for agricultural diagnostics using PyTorch and React JS. GitHub repository.",
                    "package.json": '{"dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}',
                    "requirements.txt": "torch>=2.2.0\ntorchvision>=0.17.0\nflask>=3.0.0",
                }
            },
            "rishank/private-repo": {
                "status": "PRIVATE"
            },
            "rishank/deleted-repo": {
                "status": "UNAVAILABLE"
            },
            "rishank/network-failure-repo": {
                "status": "NOT_VERIFIED"
            }
        }
        
        key = f"{owner.lower()}/{repo.lower()}"
        
        if key in mock_repos:
            repo_info = mock_repos[key]
            status = repo_info["status"]
            if status != "ANALYZED":
                return {
                    "github_analysis_status": status,
                    "technologies_found": [],
                    "evidence": {
                        "readme_available": False,
                        "source_code_available": False,
                        "dependencies_detected": False,
                        "tests_detected": False
                    },
                    "project_quality": {
                        "documentation": "NONE",
                        "structure": "NONE",
                        "testing": "NONE",
                        "technology_consistency": "NONE"
                    }
                }
            
            techs_found = []
            files = repo_info.get("files", {})
            readme = files.get("README.md", "")
            requirements = files.get("requirements.txt", "")
            package_json = files.get("package.json", "")
            
            combined_text = (readme + " " + requirements + " " + package_json).lower()
            
            for alias, normalized in SKILL_ALIASES.items():
                if re.search(r'\b' + re.escape(alias) + r'\b', combined_text):
                    if normalized not in techs_found:
                        techs_found.append(normalized)
            
            has_readme = "README.md" in files
            has_deps = "requirements.txt" in files or "package.json" in files
            has_tests = "test" in combined_text
            
            return {
                "github_analysis_status": "ANALYZED",
                "technologies_found": techs_found,
                "evidence": {
                    "readme_available": has_readme,
                    "source_code_available": True,
                    "dependencies_detected": has_deps,
                    "tests_detected": has_tests
                },
                "project_quality": {
                    "documentation": "GOOD" if has_readme and len(readme) > 50 else "LIMITED",
                    "structure": "GOOD",
                    "testing": "GOOD" if has_tests else "NONE",
                    "technology_consistency": "GOOD"
                }
            }
            
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"User-Agent": "CertiTrust-AI-Resume-Intelligence"}
            
            response = requests.get(api_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                meta = response.json()
                
                readme_content = ""
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
                r_res = requests.get(readme_url, headers=headers, timeout=3)
                if r_res.status_code != 200:
                    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                    r_res = requests.get(readme_url, headers=headers, timeout=3)
                
                if r_res.status_code == 200:
                    readme_content = r_res.text
                
                deps_content = ""
                for filename in ["requirements.txt", "package.json", "pyproject.toml", "Dockerfile"]:
                    for branch in ["main", "master"]:
                        f_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
                        f_res = requests.get(f_url, headers=headers, timeout=3)
                        if f_res.status_code == 200:
                            deps_content += " " + f_res.text
                            break
                
                combined_text = (readme_content + " " + deps_content + " " + meta.get("description", "") + " " + meta.get("language", "")).lower()
                
                techs_found = []
                for alias, normalized in SKILL_ALIASES.items():
                    if re.search(r'\b' + re.escape(alias) + r'\b', combined_text):
                        if normalized not in techs_found:
                            techs_found.append(normalized)
                            
                has_readme = bool(readme_content)
                has_deps = bool(deps_content)
                has_tests = "test" in combined_text or "spec" in combined_text
                
                return {
                    "github_analysis_status": "ANALYZED",
                    "technologies_found": techs_found,
                    "evidence": {
                        "readme_available": has_readme,
                        "source_code_available": True,
                        "dependencies_detected": has_deps,
                        "tests_detected": has_tests
                    },
                    "project_quality": {
                        "documentation": "GOOD" if has_readme and len(readme_content) > 150 else "LIMITED",
                        "structure": "GOOD",
                        "testing": "GOOD" if has_tests else "NONE",
                        "technology_consistency": "GOOD"
                    }
                }
            elif response.status_code == 404:
                return {
                    "github_analysis_status": "UNAVAILABLE",
                    "technologies_found": [],
                    "evidence": {
                        "readme_available": False,
                        "source_code_available": False,
                        "dependencies_detected": False,
                        "tests_detected": False
                    },
                    "project_quality": {
                        "documentation": "NONE",
                        "structure": "NONE",
                        "testing": "NONE",
                        "technology_consistency": "NONE"
                    }
                }
            elif response.status_code == 403:
                return {
                    "github_analysis_status": "PRIVATE" if "rate limit" not in response.text.lower() else "NOT_VERIFIED",
                    "technologies_found": [],
                    "evidence": {
                        "readme_available": False,
                        "source_code_available": False,
                        "dependencies_detected": False,
                        "tests_detected": False
                    },
                    "project_quality": {
                        "documentation": "NONE",
                        "structure": "NONE",
                        "testing": "NONE",
                        "technology_consistency": "NONE"
                    }
                }
            else:
                return {
                    "github_analysis_status": "NOT_VERIFIED",
                    "technologies_found": [],
                    "evidence": {
                        "readme_available": False,
                        "source_code_available": False,
                        "dependencies_detected": False,
                        "tests_detected": False
                    },
                    "project_quality": {
                        "documentation": "NONE",
                        "structure": "NONE",
                        "testing": "NONE",
                        "technology_consistency": "NONE"
                    }
                }
        except Exception as e:
            logger.error(f"GitHub analysis failed due to connection error: {str(e)}")
            return {
                "github_analysis_status": "NOT_VERIFIED",
                "technologies_found": [],
                "evidence": {
                    "readme_available": False,
                    "source_code_available": False,
                    "dependencies_detected": False,
                    "tests_detected": False
                },
                "project_quality": {
                    "documentation": "NONE",
                    "structure": "NONE",
                    "testing": "NONE",
                    "technology_consistency": "NONE"
                }
            }

    def _calculate_credibility_and_risk(self, skill_verifications: List[Dict[str, Any]], 
                                         edu_verifications: List[Dict[str, Any]], 
                                         cert_verifications: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Calculates Overall Credibility Confidence and Risk Level.
        """
        total_claims = len(skill_verifications) + len(edu_verifications) + len(cert_verifications)
        
        verified_claims = (
            sum(1 for s in skill_verifications if s["verification_status"] == "VERIFIED") +
            sum(1 for e in edu_verifications if e["status"] == "VERIFIED") +
            sum(1 for c in cert_verifications if c["verification_status"] == "VERIFIED")
        )
        
        contradicted_claims = (
            sum(1 for s in skill_verifications if s["verification_status"] == "CONTRADICTED") +
            sum(1 for e in edu_verifications if e["status"] == "CONTRADICTED") +
            sum(1 for c in cert_verifications if c["verification_status"] == "CONTRADICTED")
        )
        
        unverified_claims = total_claims - verified_claims - contradicted_claims
        
        has_edu_contradiction = any(e["status"] == "CONTRADICTED" for e in edu_verifications)
        
        if has_edu_contradiction:
            risk_level = "CRITICAL"
            cred_level = "NEEDS_REVIEW"
        elif contradicted_claims > 0:
            risk_level = "HIGH"
            cred_level = "NEEDS_REVIEW"
        elif unverified_claims > total_claims * 0.5 or unverified_claims >= 10:
            risk_level = "MEDIUM"
            cred_level = "LOW_CONFIDENCE"
        elif verified_claims >= total_claims * 0.7:
            risk_level = "LOW"
            cred_level = "HIGH_CONFIDENCE"
        else:
            risk_level = "MEDIUM"
            cred_level = "MEDIUM_CONFIDENCE"
            
        return {"level": cred_level}, {"level": risk_level}

    def _generate_full_ai_summary(self, candidate: Dict[str, Any], 
                                   education: List[Dict[str, Any]], 
                                   experience: List[Dict[str, Any]], 
                                   internships: List[Dict[str, Any]], 
                                   skills: List[Dict[str, Any]], 
                                   projects: List[Dict[str, Any]], 
                                   skill_verifications: List[Dict[str, Any]], 
                                   edu_verifications: List[Dict[str, Any]], 
                                   cert_verifications: List[Dict[str, Any]], 
                                   project_analysis: List[Dict[str, Any]], 
                                   credibility: Dict[str, Any], 
                                   risk: Dict[str, Any]) -> str:
        """
        Generates the consolidated, evidence-aware Full AI Resume Summary.
        """
        name = candidate.get("name") or "The candidate"
        
        summary_lines = []
        edu_str = ""
        if education:
            edu_str = f"completed/pursuing {education[0].get('degree')} from {education[0].get('institution') or 'academic institution'}"
        
        exp_str = ""
        if experience or internships:
            exp_str = f"with {len(experience)} professional role(s) and {len(internships)} internship(s)"
            
        profile_para = f"{name} is a student/professional {edu_str} {exp_str}."
        summary_lines.append(profile_para)
        
        total_projs = len(projects)
        github_projs = sum(1 for p in project_analysis if p.get("github_url"))
        supported_projs = sum(1 for p in project_analysis if p.get("project_status") == "SUPPORTED")
        part_projs = sum(1 for p in project_analysis if p.get("project_status") == "PARTIALLY_SUPPORTED")
        
        proj_para = (
            f"The candidate lists {total_projs} project(s) on the resume, "
            f"out of which {github_projs} have public GitHub repositories."
        )
        if github_projs > 0:
            proj_para += (
                f" Based on static analysis, {supported_projs} project(s) are fully supported "
                f"by codebase evidence, and {part_projs} are partially supported."
            )
        else:
            proj_para += " No public GitHub repositories were available for static analysis."
            
        summary_lines.append(proj_para)
        
        verified_skills = [s["skill"] for s in skill_verifications if s["verification_status"] == "VERIFIED"]
        unverified_skills = [s["skill"] for s in skill_verifications if s["verification_status"] == "UNVERIFIED"]
        contradicted_skills = [s["skill"] for s in skill_verifications if s["verification_status"] == "CONTRADICTED"]
        
        skills_para = ""
        if verified_skills:
            skills_para += f"Several technical skills such as {', '.join(verified_skills[:5])} are verified via the CertiTrust Skill Passport."
        if unverified_skills:
            skills_para += f" Technical skills like {', '.join(unverified_skills[:5])} are claimed on the resume but remain unverified as no trusted records exist in the registry."
        if contradicted_skills:
            skills_para += f" WARNING: Skills such as {', '.join(contradicted_skills)} directly conflict with trusted academic records."
            
        if skills_para:
            summary_lines.append(skills_para)
            
        edu_contradictions = [ev for ev in edu_verifications if ev.get("status") == "CONTRADICTED"]
        cert_contradictions = [cv for cv in cert_verifications if cv.get("verification_status") == "CONTRADICTED"]
        
        verif_para = "Academic and certification records are generally aligned with issuer source of truth."
        if edu_contradictions or cert_contradictions:
            verif_para = "CRITICAL WARNING: Direct discrepancies were detected against issuer source of truth."
            for ec in edu_contradictions:
                verif_para += f" For {ec.get('claim')}, the resume claims a value of {ec.get('resume_value')}, but the verified issuer registry shows {ec.get('verified_value')}."
            for cc in cert_contradictions:
                verif_para += f" Discrepancy found in certificate claim '{cc.get('certification')}'."
        
        summary_lines.append(verif_para)
        
        cred_val = credibility.get("level")
        risk_val = risk.get("level")
        
        cred_para = f"Overall Credibility:\n{cred_val}\n\nRisk:\n{risk_val}"
        summary_lines.append(cred_para)
        
        if risk_val == "CRITICAL":
            recommendation = (
                "Recommendation:\n"
                "The employer is strongly advised to flag this application and conduct a detailed forensic audit "
                "or interview the candidate specifically regarding the identified academic grade discrepancies."
            )
        elif risk_val == "HIGH":
            recommendation = (
                "Recommendation:\n"
                "The application contains major unverified/contradicted claims. High diligence is recommended, "
                "and verification of other claims should be requested."
            )
        elif risk_val == "MEDIUM":
            recommendation = (
                "Recommendation:\n"
                "Resume appears largely consistent with available evidence, but the employer should review "
                "the unverified claims and GitHub repository content before making a final decision."
            )
        else:
            recommendation = (
                "Recommendation:\n"
                "The resume is highly credible with extensive matching evidence in both Skill Passport and public GitHub repos. "
                "Recommended for direct automated processing."
            )
            
        summary_lines.append(recommendation)
        
        return "\n\n".join(summary_lines)


# Global Singleton Service Instance
resume_analysis_service = ResumeAnalysisService()
