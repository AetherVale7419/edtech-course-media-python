from datetime import date

from src.course_media_service import LearnerDeadline, learner_report


def test_deadline_report_marks_late_learner():
    deadline = LearnerDeadline("lee", date(2026, 9, 10))
    assert learner_report(deadline, date(2026, 9, 13))["status"] == "overdue"
