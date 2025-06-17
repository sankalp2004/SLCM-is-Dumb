# data_models.py
# Data models for structured results from the SLCM scraper
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class StudentGrade:
    subject_code: str
    subject_name: str
    credits: int
    grade: str
    grade_points: float

@dataclass
class SemesterResult:
    semester: int
    sgpa: float
    credits: int
    grades: List[StudentGrade]

@dataclass
class StudentResult:
    student_id: str
    name: str
    cgpa: float
    semesters: List[SemesterResult]
