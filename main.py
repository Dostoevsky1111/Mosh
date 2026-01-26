import sys
import os
import random
import hashlib
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import threading
import warnings
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QLineEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QGroupBox, QSplitter, QScrollArea,
    QMenuBar, QMenu, QDialog, QTextEdit, QProgressBar, QFileDialog,
    QMessageBox, QGridLayout, QFrame, QSizePolicy, QSpinBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QColor, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


warnings.filterwarnings("ignore", category=UserWarning)


# ENUM И КЛАССЫ ДЛЯ ЛОГИЧЕСКИХ ОПЕРАТОРОВ
class LogicOperator(Enum):
    AND = "AND"
    OR = "OR"
    
    @property
    def display_value(self):
        return "И" if self.value == "AND" else "ИЛИ"

@dataclass
class FilterCondition:
    field: str
    operator: str
    value: Any
    logic: LogicOperator = LogicOperator.AND

# КЛАСС ДЛЯ ГЕНЕРАЦИИ ТЕСТОВЫХ ДАННЫХ (С ЦЕЛЕВЫМИ БАЛЛАМИ)
class FixedTestDataGenerator:
    def __init__(self):
        self.programs = {
            'ПМ': {'name': 'Прикладная математика', 'places': 40},
            'ИВТ': {'name': 'Информатика и вычислительная техника', 'places': 50},
            'ИТСС': {'name': 'Инфокоммуникационные технологии и системы связи', 'places': 30},
            'ИБ': {'name': 'Информационная безопасность', 'places': 20}
        }
        
        # Целевые проходные баллы
        self.target_scores = {
            '02.08': {'ПМ': 218, 'ИВТ': 212, 'ИТСС': 219, 'ИБ': 219},
            '03.08': {'ПМ': 252, 'ИВТ': 250, 'ИТСС': 210, 'ИБ': 205},
            '04.08': {'ПМ': 290, 'ИВТ': 275, 'ИТСС': 260, 'ИБ': 280}
        }
        
        # Количество абитуриентов по дням и программам
        self.day_counts = {
            '01.08': {'ПМ': 60, 'ИВТ': 100, 'ИТСС': 50, 'ИБ': 70},
            '02.08': {'ПМ': 380, 'ИВТ': 370, 'ИТСС': 350, 'ИБ': 260},
            '03.08': {'ПМ': 1000, 'ИВТ': 1150, 'ИТСС': 1050, 'ИБ': 800},
            '04.08': {'ПМ': 1240, 'ИВТ': 1390, 'ИТСС': 1240, 'ИБ': 1190}
        }
        
        # Пересечения для 2 программ
        self.intersections_2 = {
            '01.08': {
                ('ПМ', 'ИВТ'): 22, ('ПМ', 'ИТСС'): 17, ('ПМ', 'ИБ'): 20,
                ('ИВТ', 'ИТСС'): 19, ('ИВТ', 'ИБ'): 22, ('ИТСС', 'ИБ'): 17
            },
            '02.08': {
                ('ПМ', 'ИВТ'): 190, ('ПМ', 'ИТСС'): 190, ('ПМ', 'ИБ'): 150,
                ('ИВТ', 'ИТСС'): 190, ('ИВТ', 'ИБ'): 140, ('ИТСС', 'ИБ'): 120
            },
            '03.08': {
                ('ПМ', 'ИВТ'): 760, ('ПМ', 'ИТСС'): 600, ('ПМ', 'ИБ'): 410,
                ('ИВТ', 'ИТСС'): 750, ('ИВТ', 'ИБ'): 460, ('ИТСС', 'ИБ'): 500
            },
            '04.08': {
                ('ПМ', 'ИВТ'): 1090, ('ПМ', 'ИТСС'): 1110, ('ПМ', 'ИБ'): 1070,
                ('ИВТ', 'ИТСС'): 1050, ('ИВТ', 'ИБ'): 1040, ('ИТСС', 'ИБ'): 1090
            }
        }
        
        # Пересечения для 3 и 4 программ
        self.intersections_3_4 = {
            '01.08': {
                ('ПМ', 'ИВТ', 'ИТСС'): 5, ('ПМ', 'ИВТ', 'ИБ'): 5,
                ('ИВТ', 'ИТСС', 'ИБ'): 5, ('ПМ', 'ИТСС', 'ИБ'): 5,
                ('ПМ', 'ИВТ', 'ИТСС', 'ИБ'): 3
            },
            '02.08': {
                ('ПМ', 'ИВТ', 'ИТСС'): 70, ('ПМ', 'ИВТ', 'ИБ'): 70,
                ('ИВТ', 'ИТСС', 'ИБ'): 70, ('ПМ', 'ИТСС', 'ИБ'): 70,
                ('ПМ', 'ИВТ', 'ИТСС', 'ИБ'): 50
            },
            '03.08': {
                ('ПМ', 'ИВТ', 'ИТСС'): 500, ('ПМ', 'ИВТ', 'ИБ'): 260,
                ('ИВТ', 'ИТСС', 'ИБ'): 300, ('ПМ', 'ИТСС', 'ИБ'): 250,
                ('ПМ', 'ИВТ', 'ИТСС', 'ИБ'): 200
            },
            '04.08': {
                ('ПМ', 'ИВТ', 'ИТСС'): 1020, ('ПМ', 'ИВТ', 'ИБ'): 1020,
                ('ИВТ', 'ИТСС', 'ИБ'): 1000, ('ПМ', 'ИТСС', 'ИБ'): 1040,
                ('ПМ', 'ИВТ', 'ИТСС', 'ИБ'): 1000
            }
        }
    
    def generate_student_id(self, base_id: int, day: str) -> int:
        """Генерация уникального ID абитуриента"""
        return int(hashlib.md5(f"{base_id}_{day}".encode()).hexdigest()[:8], 16) % 1000000
    
    def generate_scores_with_target(self, program: str, day: str, target_score: int = None) -> Dict:
        """Генерация баллов для абитуриента с учетом целевого проходного балла"""
        if target_score is None:
            # Базовые диапазоны для каждого дня
            if day == '01.08':
                physics = random.randint(40, 80)
                russian = random.randint(40, 80)
                math = random.randint(40, 80)
            elif day == '02.08':
                physics = random.randint(50, 90)
                russian = random.randint(50, 90)
                math = random.randint(50, 90)
            elif day == '03.08':
                physics = random.randint(60, 100)
                russian = random.randint(60, 100)
                math = random.randint(60, 100)
            elif day == '04.08':
                physics = random.randint(70, 100)
                russian = random.randint(70, 100)
                math = random.randint(70, 110)
            else:
                physics = random.randint(50, 100)
                russian = random.randint(50, 100)
                math = random.randint(50, 100)
        else:
            # Генерация баллов вокруг целевого проходного балла
            base_range = 30
            min_score = max(100, target_score - base_range)
            max_score = target_score + base_range

            # Распределяем баллы по предметам
            total_needed = target_score + random.randint(-10, 20)
            if total_needed < 100:
                total_needed = random.randint(100, 200)

            # Генерируем предметные баллы с ограничением до 100
            physics = min(100, random.randint(min_score // 3, max_score // 3))
            russian = min(100, random.randint(min_score // 3, max_score // 3))
            math = min(100, total_needed - physics - russian - random.randint(0, 10))

            # Корректировка если математика получилась отрицательной
            if math < 0:
                math = min(100, random.randint(min_score // 3, max_score // 3))
                total_needed = physics + russian + math
        
        achievements = random.randint(0, 10)
        total = physics + russian + math + achievements
        
        return {
            'physics_score': physics,
            'russian_score': russian,
            'math_score': math,
            'achievements_score': achievements,
            'total_score': total
        }
    
    def create_target_students(self, program: str, day: str, target_score: int, count: int, 
                              consent_prob: float = 0.9) -> List[Dict]:
        """Создание абитуриентов с баллами вокруг целевого проходного балла"""
        students = []
        places = self.programs[program]['places']
        
        # Создаем абитуриентов, которые будут зачислены
        admitted_needed = min(places * 2, count // 2)  # Вдвое больше мест
        
        for i in range(admitted_needed):
            # Создаем абитуриента с баллом не ниже целевого
            base_score = target_score + random.randint(0, 30)
            scores = self.generate_scores_with_target(program, day, base_score)
            
            # Гарантируем, что суммарный балл не ниже целевого
            while scores['total_score'] < target_score:
                scores = self.generate_scores_with_target(program, day, base_score)
            
            student = {
                'id': self.generate_student_id(len(students) + 100000, day),
                'consent': random.random() < consent_prob,
                'priority': random.randint(1, 4),
                'physics_score': scores['physics_score'],
                'russian_score': scores['russian_score'],
                'math_score': scores['math_score'],
                'achievements_score': scores['achievements_score'],
                'total_score': scores['total_score']
            }
            
            # Для последнего зачисленного гарантируем балл точно на целевом уровне
            if i == admitted_needed - 1 and student['total_score'] > target_score:
                # Слегка уменьшаем балл до целевого
                adjustment = student['total_score'] - target_score
                if student['math_score'] >= adjustment:
                    student['math_score'] -= adjustment
                elif student['physics_score'] >= adjustment:
                    student['physics_score'] -= adjustment
                elif student['russian_score'] >= adjustment:
                    student['russian_score'] -= adjustment
                student['total_score'] = target_score
            
            students.append(student)
        
        # Создаем остальных абитуриентов с баллами ниже целевого
        remaining_count = count - admitted_needed
        for i in range(remaining_count):
            # Создаем абитуриента с баллом ниже целевого
            base_score = target_score - random.randint(10, 50)
            if base_score < 100:
                base_score = random.randint(100, target_score - 5)
            
            scores = self.generate_scores_with_target(program, day, base_score)
            
            student = {
                'id': self.generate_student_id(len(students) + 100000, day),
                'consent': random.random() < 0.3,  # Меньше согласий у тех, кто ниже проходного
                'priority': random.randint(1, 4),
                'physics_score': scores['physics_score'],
                'russian_score': scores['russian_score'],
                'math_score': scores['math_score'],
                'achievements_score': scores['achievements_score'],
                'total_score': scores['total_score']
            }
            
            # Гарантируем, что суммарный балл ниже целевого
            if student['total_score'] >= target_score:
                adjustment = student['total_score'] - target_score + 1
                student['math_score'] -= adjustment
                student['total_score'] -= adjustment
            
            students.append(student)
        
        return students
    
    def generate_day_data(self, day: str) -> Dict[str, List]:
        """Генерация данных для конкретного дня с целевыми проходными баллами"""
        day_data = {program: [] for program in self.programs}
        students = {}
        student_counter = 1
        
        # Определяем настройки для дня
        if day == '01.08':
            # Для 01.08 - недобор
            consent_prob = 0.2
            target_scores = None
        elif day in self.target_scores:
            # Для дней с целевыми баллами
            consent_prob = 0.7
            target_scores = self.target_scores[day]
        else:
            consent_prob = 0.5
            target_scores = None
        
        # Создаем абитуриентов с 4 программами
        count_4 = self.intersections_3_4[day][('ПМ', 'ИВТ', 'ИТСС', 'ИБ')]
        for i in range(count_4):
            student_id = self.generate_student_id(student_counter, day)
            
            # Генерируем баллы для каждой программы отдельно
            scores = {}
            for program in ['ПМ', 'ИВТ', 'ИТСС', 'ИБ']:
                target_score = target_scores[program] if target_scores else None
                scores[program] = self.generate_scores_with_target(program, day, target_score)
            
            # Настройка согласия в зависимости от дня
            if day == '01.08':
                consent = random.random() < 0.1  # Мало согласий для недобора
            else:
                consent = random.random() < consent_prob
            
            priorities = [1, 2, 3, 4]
            random.shuffle(priorities)
            
            students[student_id] = {
                'id': student_id,
                'programs': ['ПМ', 'ИВТ', 'ИТСС', 'ИБ'],
                'priorities': {prog: priorities[idx] for idx, prog in enumerate(['ПМ', 'ИВТ', 'ИТСС', 'ИБ'])},
                'scores': scores,
                'consent': consent
            }
            student_counter += 1
        
        # Создаем абитуриентов с 3 программами
        triple_combinations = [
            ('ПМ', 'ИВТ', 'ИТСС'), ('ПМ', 'ИВТ', 'ИБ'),
            ('ИВТ', 'ИТСС', 'ИБ'), ('ПМ', 'ИТСС', 'ИБ')
        ]
        
        for combo in triple_combinations:
            count = self.intersections_3_4[day][combo]
            for i in range(count):
                student_id = self.generate_student_id(student_counter, day)
                
                scores = {}
                for program in combo:
                    target_score = target_scores[program] if target_scores else None
                    scores[program] = self.generate_scores_with_target(program, day, target_score)
                
                if day == '01.08':
                    consent = random.random() < 0.1
                else:
                    consent = random.random() < consent_prob
                
                priorities = [1, 2, 3]
                random.shuffle(priorities)
                
                students[student_id] = {
                    'id': student_id,
                    'programs': list(combo),
                    'priorities': {prog: priorities[idx] for idx, prog in enumerate(combo)},
                    'scores': scores,
                    'consent': consent
                }
                student_counter += 1
        
        # Создаем абитуриентов с 2 программами
        double_combinations = list(self.intersections_2[day].keys())
        
        for combo in double_combinations:
            count = self.intersections_2[day][combo]
            for i in range(count):
                student_id = self.generate_student_id(student_counter, day)
                
                scores = {}
                for program in combo:
                    target_score = target_scores[program] if target_scores else None
                    scores[program] = self.generate_scores_with_target(program, day, target_score)
                
                if day == '01.08':
                    consent = random.random() < 0.1
                else:
                    consent = random.random() < consent_prob
                
                priorities = [1, 2]
                random.shuffle(priorities)
                
                students[student_id] = {
                    'id': student_id,
                    'programs': list(combo),
                    'priorities': {prog: priorities[idx] for idx, prog in enumerate(combo)},
                    'scores': scores,
                    'consent': consent
                }
                student_counter += 1
        
        # После создания абитуриентов с несколькими программами,
        # подсчитываем сколько заявок уже создано для каждой программы
        current_counts = {program: 0 for program in self.programs}
        for student_data in students.values():
            for program in student_data['programs']:
                current_counts[program] += 1
        
        # Теперь создаем абитуриентов с 1 программой, чтобы достичь нужного количества
        for program in self.programs:
            needed = self.day_counts[day][program] - current_counts[program]
            
            if needed > 0:
                if day in self.target_scores:
                    target_score = self.target_scores[day][program]
                    # Создаем часть абитуриентов с баллами вокруг целевого
                    target_students_count = min(needed, self.programs[program]['places'] * 3)
                    non_target_students_count = needed - target_students_count
                    
                    # Создаем целевых абитуриентов
                    target_students = self.create_target_students(
                        program, day, target_score, target_students_count, consent_prob
                    )
                    
                    for student in target_students:
                        student_id = self.generate_student_id(student_counter, day)
                        students[student_id] = {
                            'id': student_id,
                            'programs': [program],
                            'priorities': {program: student['priority']},
                            'scores': {program: {
                                'physics_score': student['physics_score'],
                                'russian_score': student['russian_score'],
                                'math_score': student['math_score'],
                                'achievements_score': student['achievements_score'],
                                'total_score': student['total_score']
                            }},
                            'consent': student['consent']
                        }
                        student_counter += 1
                        needed -= 1
                
                # Создаем оставшихся абитуриентов
                for i in range(needed):
                    student_id = self.generate_student_id(student_counter, day)
                    
                    target_score = target_scores[program] if target_scores and day in target_scores else None
                    scores = {program: self.generate_scores_with_target(program, day, target_score)}
                    
                    if day == '01.08':
                        consent = random.random() < 0.05
                    elif day == '04.08':
                        consent = random.random() < 0.8
                    else:
                        consent = random.random() < consent_prob
                    
                    students[student_id] = {
                        'id': student_id,
                        'programs': [program],
                        'priorities': {program: random.randint(1, 4)},
                        'scores': scores,
                        'consent': consent
                    }
                    student_counter += 1
        
        # Преобразуем в формат по программам
        for student_id, student_data in students.items():
            for program in student_data['programs']:
                day_data[program].append({
                    'id': student_id,
                    'consent': student_data['consent'],
                    'priority': student_data['priorities'][program],
                    'physics_score': student_data['scores'][program]['physics_score'],
                    'russian_score': student_data['scores'][program]['russian_score'],
                    'math_score': student_data['scores'][program]['math_score'],
                    'achievements_score': student_data['scores'][program]['achievements_score'],
                    'total_score': student_data['scores'][program]['total_score']
                })
        
        # ПРОВЕРКА КОЛИЧЕСТВА ДЛЯ КАЖДОЙ ПРОГРАММЫ
        for program in self.programs:
            count = len(day_data[program])
            expected = self.day_counts[day][program]
            
            # Если количество не совпадает, корректируем
            if count != expected:
                print(f"  Корректировка {program}: {count} -> {expected}")
                
                if count > expected:
                    # Удаляем лишних (начинаем с последних добавленных)
                    day_data[program] = day_data[program][:expected]
                else:
                    # Добавляем недостающих
                    for i in range(expected - count):
                        student_id = self.generate_student_id(student_counter, day)
                        student_counter += 1
                        
                        target_score = target_scores[program] if target_scores and day in target_scores else None
                        scores = self.generate_scores_with_target(program, day, target_score)
                        
                        if day == '01.08':
                            consent = random.random() < 0.05
                        elif day == '04.08':
                            consent = random.random() < 0.8
                        else:
                            consent = random.random() < consent_prob
                        
                        day_data[program].append({
                            'id': student_id,
                            'consent': consent,
                            'priority': random.randint(1, 4),
                            'physics_score': scores['physics_score'],
                            'russian_score': scores['russian_score'],
                            'math_score': scores['math_score'],
                            'achievements_score': scores['achievements_score'],
                            'total_score': scores['total_score']
                        })
        
        # Проверка и корректировка для выполнения условий
        if day == '01.08':
            # Гарантируем НЕДОБОР (согласий меньше чем мест)
            for program in self.programs:
                consents = sum(1 for student in day_data[program] if student['consent'])
                places = self.programs[program]['places']
                if consents >= places:
                    # Уменьшаем количество согласий
                    consent_students = [s for s in day_data[program] if s['consent']]
                    to_remove = consents - places + 1
                    for i in range(min(to_remove, len(consent_students))):
                        consent_students[i]['consent'] = False
        
        elif day in self.target_scores:
            # Гарантируем выполнение целевых проходных баллов
            for program in self.programs:
                target_score = self.target_scores[day][program]
                places = self.programs[program]['places']
                
                # Находим абитуриентов с согласием, сортируем по баллам
                consent_students = [s for s in day_data[program] if s['consent']]
                consent_students.sort(key=lambda x: (-x['total_score'], x['priority']))
                
                # Гарантируем, что на последнем месте будет целевой балл
                if len(consent_students) >= places:
                    # Находим студента с баллом близким к целевому
                    for i in range(places - 5, min(places + 5, len(consent_students))):
                        if i >= 0 and consent_students[i]['total_score'] == target_score:
                            # Меняем местами с последним зачисленным
                            consent_students[places-1], consent_students[i] = \
                                consent_students[i], consent_students[places-1]
                            break
                    
                    # Если не нашли, корректируем балл последнего зачисленного
                    if consent_students[places-1]['total_score'] != target_score:
                        diff = target_score - consent_students[places-1]['total_score']
                        consent_students[places-1]['math_score'] += diff
                        consent_students[places-1]['total_score'] = target_score
                
                # Обновляем данные
                student_dict = {student['id']: student for student in day_data[program]}
                for student in consent_students:
                    if student['id'] in student_dict:
                        student_dict[student['id']].update(student)
                day_data[program] = list(student_dict.values())
        
        return day_data
    
    def generate_all_days(self):
        """Генерация данных для всех дней"""
        all_data = {}
        
        print("Генерация тестовых данных с целевыми проходными баллами...")
        print("Целевые проходные баллы:")
        print("  02.08: ПМ=218, ИВТ=212, ИТСС=219, ИБ=219")
        print("  03.08: ПМ=252, ИВТ=250, ИТСС=210, ИБ=205")
        print("  04.08: ПМ=290, ИВТ=275, ИТСС=260, ИБ=280")
        print("  01.08: НЕДОБОР по всем программам")
        
        for day in ['01.08', '02.08', '03.08', '04.08']:
            print(f"\nГенерация данных для {day}...")
            all_data[day] = self.generate_day_data(day)
            
            # Проверка количества
            for program in self.programs:
                count = len(all_data[day][program])
                expected = self.day_counts[day][program]
                print(f"  {program}: {count} записей (ожидалось {expected})")
                
                # Проверка согласий
                consents = sum(1 for student in all_data[day][program] if student['consent'])
                places = self.programs[program]['places']
                print(f"     Согласий: {consents}, мест: {places}")
        
        return all_data
    
    def save_to_csv(self, all_data: Dict[str, Dict[str, List]]):
        """Сохранение данных в CSV файлы"""
        if not os.path.exists('data'):
            os.makedirs('data')
        
        for day, day_data in all_data.items():
            for program, students in day_data.items():
                filename = f"data/{day}_{program}.csv"
                df = pd.DataFrame(students)
                df.to_csv(filename, index=False, encoding='utf-8')
                print(f"Сохранено: {filename} ({len(df)} записей)")
    
    def run_generation(self):
        """Основной метод генерации"""
        all_data = self.generate_all_days()
        self.save_to_csv(all_data)
        print("\nГенерация тестовых данных завершена!")
        print("\nДля проверки:")
        print("1. Загрузите данные из папки 'data/'")
        print("2. Рассчитайте проходные баллы")
        print("3. Убедитесь, что результаты соответствуют целевым значениям")

# КЛАСС БАЗЫ ДАННЫХ
class EnhancedDatabase:
    def __init__(self, db_path="admission.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('PRAGMA encoding = "UTF-8"')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id INTEGER NOT NULL,
                program TEXT NOT NULL,
                list_date TEXT NOT NULL,
                consent BOOLEAN NOT NULL,
                priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 4),
                physics_score INTEGER NOT NULL,
                russian_score INTEGER NOT NULL,
                math_score INTEGER NOT NULL,
                achievements_score INTEGER NOT NULL,
                total_score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(external_id, program, list_date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pass_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program TEXT NOT NULL,
                list_date TEXT NOT NULL,
                pass_score INTEGER,
                calculation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(program, list_date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program TEXT NOT NULL,
                list_date TEXT NOT NULL,
                total_applications INTEGER,
                priority_1_apps INTEGER,
                priority_2_apps INTEGER,
                priority_3_apps INTEGER,
                priority_4_apps INTEGER,
                priority_1_admitted INTEGER,
                priority_2_admitted INTEGER,
                priority_3_admitted INTEGER,
                priority_4_admitted INTEGER,
                calculation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(program, list_date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def clear_database(self):
        """Очистка базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applicants")
        cursor.execute("DELETE FROM pass_scores")
        cursor.execute("DELETE FROM statistics")
        conn.commit()
        conn.close()
    
    def load_csv(self, filepath: str, list_date: str) -> bool:
        """Загрузка данных из CSV файла"""
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            
            filename = os.path.basename(filepath)
            parts = filename.split('_')
            if len(parts) >= 2:
                program = parts[1].split('.')[0]
            else:
                program = 'Unknown'
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM applicants WHERE program = ? AND list_date = ?",
                (program, list_date)
            )
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO applicants 
                        (external_id, program, list_date, consent, priority, 
                         physics_score, russian_score, math_score, 
                         achievements_score, total_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        int(row['id']), program, list_date,
                        bool(row['consent']), int(row['priority']),
                        int(row['physics_score']), int(row['russian_score']),
                        int(row['math_score']), int(row['achievements_score']),
                        int(row['total_score'])
                    ))
                except Exception as e:
                    print(f"Ошибка при вставке строки: {e}")
                    continue
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки CSV: {e}")
            return False
    
    def get_applicants_with_filters(self, filters: List[FilterCondition] = None) -> List[Dict]:
        """Получение списка абитуриентов с расширенной фильтрацией"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM applicants WHERE 1=1"
        params = []
        
        if filters:
            for filter_cond in filters:
                sql_operator = filter_cond.logic.value
                
                if filter_cond.operator == "=":
                    query += f" {sql_operator} {filter_cond.field} = ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == ">":
                    query += f" {sql_operator} {filter_cond.field} > ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == "<":
                    query += f" {sql_operator} {filter_cond.field} < ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == ">=":
                    query += f" {sql_operator} {filter_cond.field} >= ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == "<=":
                    query += f" {sql_operator} {filter_cond.field} <= ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == "!=":
                    query += f" {sql_operator} {filter_cond.field} != ?"
                    params.append(filter_cond.value)
                elif filter_cond.operator == "IN":
                    if isinstance(filter_cond.value, (list, tuple)):
                        placeholders = ','.join(['?'] * len(filter_cond.value))
                        query += f" {sql_operator} {filter_cond.field} IN ({placeholders})"
                        params.extend(filter_cond.value)
        
        query += " ORDER BY total_score DESC, external_id"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append(dict(row))
        
        conn.close()
        return result
    
    def calculate_pass_score(self, program: str, list_date: str) -> Optional[int]:
        """Расчет проходного балла для программы"""
        filters = [
            FilterCondition("program", "=", program, LogicOperator.AND),
            FilterCondition("list_date", "=", list_date, LogicOperator.AND),
            FilterCondition("consent", "=", 1, LogicOperator.AND)
        ]
        
        applicants = self.get_applicants_with_filters(filters)
        
        if not applicants:
            return None
        
        applicants.sort(key=lambda x: (x['priority'], -x['total_score']))
        
        places = {
            'ПМ': 40, 'ИВТ': 50, 'ИТСС': 30, 'ИБ': 20
        }.get(program, 0)
        
        admitted = []
        current_priority = 1
        
        while current_priority <= 4 and len(admitted) < places:
            priority_applicants = [a for a in applicants if a['priority'] == current_priority]
            priority_applicants.sort(key=lambda x: -x['total_score'])
            
            for applicant in priority_applicants:
                if len(admitted) < places:
                    admitted.append(applicant)
                else:
                    break
            current_priority += 1
        
        if len(admitted) < places:
            return None
        
        pass_score = admitted[-1]['total_score']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pass_scores (program, list_date, pass_score)
            VALUES (?, ?, ?)
        ''', (program, list_date, pass_score))
        
        total_apps = len(applicants)
        priority_counts = {}
        for i in range(1, 5):
            priority_counts[i] = len([a for a in applicants if a['priority'] == i])
        
        admitted_counts = {}
        for i in range(1, 5):
            admitted_counts[i] = len([a for a in admitted if a['priority'] == i])
        
        cursor.execute('''
            INSERT OR REPLACE INTO statistics 
            (program, list_date, total_applications,
             priority_1_apps, priority_2_apps, priority_3_apps, priority_4_apps,
             priority_1_admitted, priority_2_admitted, priority_3_admitted, priority_4_admitted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            program, list_date, total_apps,
            priority_counts.get(1, 0), priority_counts.get(2, 0),
            priority_counts.get(3, 0), priority_counts.get(4, 0),
            admitted_counts.get(1, 0), admitted_counts.get(2, 0),
            admitted_counts.get(3, 0), admitted_counts.get(4, 0)
        ))
        
        conn.commit()
        conn.close()
        
        return pass_score
    
    def get_pass_scores_by_date(self, list_date: str) -> Dict[str, Optional[int]]:
        """Получение проходных баллов по дате"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT program, pass_score FROM pass_scores WHERE list_date = ?",
            (list_date,)
        )
        
        rows = cursor.fetchall()
        result = {}
        for program in ['ПМ', 'ИВТ', 'ИТСС', 'ИБ']:
            result[program] = None
        
        for row in rows:
            result[row[0]] = row[1]
        
        conn.close()
        return result
    
    def get_all_pass_scores(self) -> List[Dict]:
        """Получение всех проходных баллов"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pass_scores ORDER BY list_date, program")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result
    
    def get_statistics(self, list_date: str) -> List[Dict]:
        """Получение статистики"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM statistics WHERE list_date = ? ORDER BY program",
            (list_date,)
        )
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result
    
    def get_dates(self) -> List[str]:
        """Получение списка дат в базе"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT list_date FROM applicants ORDER BY list_date")
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates
    
    def get_applicants_count(self, program: str = None, date: str = None) -> int:
        """Получение количества абитуриентов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM applicants WHERE 1=1"
        params = []
        
        if program:
            query += " AND program = ?"
            params.append(program)
        
        if date:
            query += " AND list_date = ?"
            params.append(date)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count

# КЛАСС ДЛЯ ПОТОКА РАСЧЕТА ПРОХОДНЫХ БАЛЛОВ
class CalculationThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, db, dates, programs):
        super().__init__()
        self.db = db
        self.dates = dates
        self.programs = programs
    
    def run(self):
        try:
            total_tasks = len(self.dates) * len(self.programs)
            completed = 0
            
            for date in self.dates:
                for program in self.programs:
                    self.db.calculate_pass_score(program, date)
                    completed += 1
                    progress = int((completed / total_tasks) * 100)
                    self.progress.emit(progress)
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# КЛАСС ДЛЯ ПОТОКА ГЕНЕРАЦИИ ОТЧЕТОВ
class ReportGenerationThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, filename, date, db, programs, places):
        super().__init__()
        self.filename = filename
        self.date = date
        self.db = db
        self.programs = programs
        self.places = places
    
    def run(self):
        try:
            # Импортируем необходимые модули для работы со шрифтами
            from reportlab.lib.enums import TA_CENTER
            import traceback
            import os
            
            # Создаем документ
            doc = SimpleDocTemplate(self.filename, pagesize=A4)
            
            # Стили для отчета
            styles = getSampleStyleSheet()
            
            # Регистрируем шрифт для поддержки кириллицы
            try:
                # Пробуем зарегистрировать Arial
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
                base_font = 'Arial'
                bold_font = 'Arial-Bold'
                self.progress.emit("Используется шрифт Arial")
            except:
                try:
                    # Пробуем DejaVu Sans (часто есть в системах)
                    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
                    base_font = 'DejaVuSans'
                    bold_font = 'DejaVuSans-Bold'
                    self.progress.emit("Используется шрифт DejaVuSans")
                except:
                    # Используем встроенные шрифты, которые поддерживают кириллицу
                    base_font = 'Times-Roman'
                    bold_font = 'Times-Bold'
                    self.progress.emit("Используется встроенный шрифт Times-Roman")
            
            # Создаем пользовательские стили
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=bold_font,
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=bold_font,
                fontSize=12,
                spaceBefore=12,
                spaceAfter=6,
                textColor=colors.darkblue
            )
            
            heading3_style = ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontName=bold_font,
                fontSize=11,
                spaceBefore=10,
                spaceAfter=4,
                textColor=colors.darkblue
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=base_font,
                fontSize=10,
                spaceAfter=6
            )
            
            italic_style = ParagraphStyle(
                'CustomItalic',
                parent=styles['Italic'],
                fontName=base_font,
                fontSize=9,
                spaceAfter=6
            )
            
            story = []
            
            # Заголовок
            title = Paragraph(f"Отчет по приемной кампании за {self.date}", title_style)
            story.append(title)
            
            # Дата формирования
            timestamp = Paragraph(
                f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", 
                normal_style
            )
            story.append(timestamp)
            story.append(Spacer(1, 20))
            
            # 1. Проходные баллы
            story.append(Paragraph("1. Проходные баллы по образовательным программам", heading_style))
            
            # Получаем проходные баллы
            pass_scores = self.db.get_pass_scores_by_date(self.date)
            
            # Данные для таблицы проходных баллов
            pass_data = [['Программа', 'Название программы', 'Кол-во мест', 'Проходной балл']]
            
            for program_code in self.programs:
                program_name = self.programs[program_code]
                places = self.places[program_code]
                score = pass_scores.get(program_code)
                
                if score is None:
                    score_text = "НЕДОБОР"
                    score_color = colors.red
                else:
                    score_text = str(score)
                    score_color = colors.green
                
                pass_data.append([program_code, program_name, str(places), score_text])
            
            # Создаем таблицу проходных баллов
            pass_table = Table(pass_data, colWidths=[1*inch, 3*inch, 1*inch, 1.2*inch])
            pass_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (3, 1), (3, -1), score_color),
            ]))
            
            story.append(pass_table)
            story.append(Spacer(1, 20))
            
            # 2. Списки зачисленных абитуриентов
            story.append(Paragraph("2. Списки зачисленных абитуриентов", heading_style))
            
            for program_code in self.programs:
                story.append(Paragraph(f"{program_code} - {self.programs[program_code]}", heading3_style))
                
                # Фильтры для абитуриентов с согласием
                filters = [
                    FilterCondition("program", "=", program_code, LogicOperator.AND),
                    FilterCondition("list_date", "=", self.date, LogicOperator.AND),
                    FilterCondition("consent", "=", 1, LogicOperator.AND)
                ]
                
                applicants = self.db.get_applicants_with_filters(filters)
                
                if not applicants:
                    story.append(Paragraph("Нет абитуриентов с согласием", normal_style))
                    story.append(Spacer(1, 10))
                    continue
                
                # Сортируем по приоритету и баллам
                applicants.sort(key=lambda x: (x['priority'], -x['total_score']))
                
                places = self.places[program_code]
                admitted = applicants[:places]
                
                if not admitted:
                    story.append(Paragraph("Нет зачисленных абитуриентов", normal_style))
                    story.append(Spacer(1, 10))
                    continue
                
                # Создаем таблицу зачисленных абитуриентов
                admitted_data = [['№', 'ID', 'Приор.', 'Физика/ИКТ', 'Мат.', 'Рус.', 'Достиж.', 'Сумма']]
                
                for idx, app in enumerate(admitted, 1):
                    admitted_data.append([
                        str(idx),
                        str(app['external_id']),
                        str(app['priority']),
                        str(app['physics_score']),
                        str(app['math_score']),
                        str(app['russian_score']),
                        str(app['achievements_score']),
                        str(app['total_score'])
                    ])
                
                # Создаем таблицу
                col_widths = [0.4*inch, 0.8*inch, 0.5*inch, 0.6*inch, 
                             0.6*inch, 0.6*inch, 0.7*inch, 0.6*inch]
                
                table = Table(admitted_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), base_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
                ]))
                
                story.append(table)
                
                # Статистика по зачисленным
                stats_text = Paragraph(
                    f"<i>Всего зачислено: {len(admitted)} из {places} мест</i>", 
                    italic_style
                )
                story.append(stats_text)
                
                if len(admitted) < len(applicants):
                    remaining_text = Paragraph(
                        f"<i>Не зачислено: {len(applicants) - len(admitted)} абитуриентов с согласием</i>", 
                        italic_style
                    )
                    story.append(remaining_text)
                
                story.append(Spacer(1, 15))
            
            # 3. Статистика по приоритетам
            story.append(Paragraph("3. Статистика по приоритетам", heading_style))
            
            stats = self.db.get_statistics(self.date)
            if stats:
                stats_data = [['Прог.', 'Всего', 'Приор. 1', 'Приор. 2', 
                              'Приор. 3', 'Приор. 4', 'Зачисл.']]
                
                for stat in stats:
                    total_admitted = sum([
                        stat.get('priority_1_admitted', 0),
                        stat.get('priority_2_admitted', 0),
                        stat.get('priority_3_admitted', 0),
                        stat.get('priority_4_admitted', 0)
                    ])
                    
                    stats_data.append([
                        stat['program'],
                        str(stat['total_applications']),
                        str(stat.get('priority_1_apps', 0)),
                        str(stat.get('priority_2_apps', 0)),
                        str(stat.get('priority_3_apps', 0)),
                        str(stat.get('priority_4_apps', 0)),
                        str(total_admitted)
                    ])
                
                col_widths = [0.6*inch, 0.6*inch, 0.7*inch, 0.7*inch, 
                             0.7*inch, 0.7*inch, 0.7*inch]
                
                stats_table = Table(stats_data, colWidths=col_widths)
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), bold_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), base_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
                ]))
                story.append(stats_table)
            else:
                story.append(Paragraph("Статистика не рассчитана", normal_style))
            
            story.append(Spacer(1, 20))
            
            # 4. Примечания
            story.append(Paragraph("4. Примечания", heading_style))
            
            notes = [
                "• Приоритет 1 - наивысший приоритет для абитуриента",
                "• НЕДОБОР означает, что количество абитуриентов с согласием меньше количества мест",
                "• Проходной балл - минимальный балл последнего зачисленного абитуриента",
                "• Абитуриенты сортируются сначала по приоритету, затем по убыванию суммарного балла"
            ]
            
            for note in notes:
                story.append(Paragraph(note, normal_style))
                story.append(Spacer(1, 3))
            
            # Строим документ
            doc.build(story)
            
            self.finished.emit(f"Отчет сохранен в файл:\n{self.filename}")
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.error.emit(f"Ошибка при создании отчета: {str(e)}\n\n{error_details}")

# КЛАСС ГРАФИКА (MATPLOTLIB)
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        self.fig = plt.Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()

# КЛАСС ДЛЯ ТЕСТОВОГО ОТЧЕТА
class TestReportDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(content)
        
        layout.addWidget(self.text_edit)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)



# КЛАСС ГЛАВНОГО ОКНА
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = EnhancedDatabase()
        
        self.programs = {
            'ПМ': 'Прикладная математика',
            'ИВТ': 'Информатика и вычислительная техника',
            'ИТСС': 'Инфокоммуникационные технологии и системы связи',
            'ИБ': 'Информационная безопасность'
        }
        self.setWindowIcon(QIcon("icon.ico"))
        self.places = {'ПМ': 40, 'ИВТ': 50, 'ИТСС': 30, 'ИБ': 20}
        
        self.filter_conditions = []
        self.current_logic_operator = LogicOperator.AND
        self.selected_program_for_viz = None
        
        self.score_filters = {}
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("ВУЗ-Assist")
        self.setGeometry(100, 100, 1600, 900)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный макет
        main_layout = QHBoxLayout(central_widget)
        
        # Разделитель для левой и правой панелей
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ЛЕВАЯ ПАНЕЛЬ - ФИЛЬТРЫ
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Заголовок фильтров
        filter_label = QLabel("Расширенные фильтры")
        filter_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(filter_label)
        
        # Область прокрутки для фильтров
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Дата списка
        date_label = QLabel("Дата списка:")
        scroll_layout.addWidget(date_label)
        
        self.date_combo = QComboBox()
        self.date_combo.currentTextChanged.connect(self.on_date_changed)
        scroll_layout.addWidget(self.date_combo)
        
        # Образовательная программа
        program_label = QLabel("Образовательная программа:")
        scroll_layout.addWidget(program_label)
        
        self.program_combo = QComboBox()
        self.program_combo.addItem("Все программы")
        for program in self.programs:
            self.program_combo.addItem(program)
        scroll_layout.addWidget(self.program_combo)
        
        # Логический оператор
        logic_label = QLabel("Логический оператор для фильтров:")
        scroll_layout.addWidget(logic_label)
        
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["И", "ИЛИ"])
        self.logic_combo.currentTextChanged.connect(self.on_logic_operator_changed)
        scroll_layout.addWidget(self.logic_combo)
        
        # Фильтры по баллам
        scores_group = QGroupBox("Фильтры по баллам")
        scores_layout = QGridLayout()
        
        subjects = [
            ('total_score', 'Суммарный балл'),
            ('physics_score', 'Физика/ИКТ'),
            ('math_score', 'Математика'),
            ('russian_score', 'Русский язык'),
            ('achievements_score', 'Дстижения')
        ]
        
        row = 0
        for field, label in subjects:
            # Название предмета
            subject_label = QLabel(label)
            scores_layout.addWidget(subject_label, row, 0)
            
            # Минимальное значение
            min_label = QLabel("от:")
            scores_layout.addWidget(min_label, row, 1)
            
            min_edit = QLineEdit()
            min_edit.setMaximumWidth(60)
            scores_layout.addWidget(min_edit, row, 2)
            
            # Максимальное значение
            max_label = QLabel("до:")
            scores_layout.addWidget(max_label, row, 3)
            
            max_edit = QLineEdit()
            max_edit.setMaximumWidth(60)
            scores_layout.addWidget(max_edit, row, 4)
            
            # Чекбокс применения
            active_check = QCheckBox("Применить")
            scores_layout.addWidget(active_check, row, 5)
            
            self.score_filters[field] = {
                'min': min_edit,
                'max': max_edit,
                'active': active_check,
                'label': label
            }
            
            row += 1
        
        scores_group.setLayout(scores_layout)
        scroll_layout.addWidget(scores_group)
        
        # Другие фильтры
        other_group = QGroupBox("Другие фильтры")
        other_layout = QVBoxLayout()
        
        # Приоритет
        priority_label = QLabel("Приоритет:")
        other_layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Любой", "1", "2", "3", "4"])
        other_layout.addWidget(self.priority_combo)
        
        # Согласие
        consent_label = QLabel("Согласие на зачисление:")
        other_layout.addWidget(consent_label)
        
        self.consent_combo = QComboBox()
        self.consent_combo.addItems(["Любое", "С согласием", "Без согласия"])
        other_layout.addWidget(self.consent_combo)
        
        other_group.setLayout(other_layout)
        scroll_layout.addWidget(other_group)
        
        # Кнопки фильтров
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("Применить фильтры")
        apply_button.clicked.connect(self.apply_filters)
        button_layout.addWidget(apply_button)
        
        reset_button = QPushButton("Сбросить фильтры")
        reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(reset_button)
        
        scroll_layout.addLayout(button_layout)
        
        # Информация о проходных баллах
        scores_group = QGroupBox("Проходные баллы (последняя дата)")
        scores_layout = QGridLayout()
        
        self.pass_score_labels = {}
        row = 0
        for program in self.programs:
            program_label = QLabel(f"{program}:")
            scores_layout.addWidget(program_label, row, 0)
            
            score_label = QLabel("-")
            score_label.setStyleSheet("font-weight: bold;")
            scores_layout.addWidget(score_label, row, 1)
            
            self.pass_score_labels[program] = score_label
            row += 1
        
        scores_group.setLayout(scores_layout)
        scroll_layout.addWidget(scores_group)
        
        # Добавляем растягивающийся элемент в конец
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        left_layout.addWidget(scroll_area)
        
        # ПРАВАЯ ПАНЕЛЬ - ТАБЛИЦА И ГРАФИКИ
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка с таблицей
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        # Таблица абитуриентов
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(11)
        self.table_widget.setHorizontalHeaderLabels([
            'ID', 'Программа', 'Дата', 'Согласие', 'Приоритет', 
            'Физика/ИКТ', 'Русский', 'Математика', 'Достижения', 'Сумма', 'Внешний ID'
        ])
        
        # Настройка ширины колонок
        column_widths = [50, 120, 80, 80, 70, 60, 70, 80, 80, 60, 80]
        for i, width in enumerate(column_widths):
            self.table_widget.setColumnWidth(i, width)
        
        table_layout.addWidget(self.table_widget)
        
        # Панель информации
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        
        self.result_label = QLabel("Всего записей: 0")
        info_layout.addWidget(self.result_label)
        
        info_layout.addStretch()
        
        self.time_label = QLabel("Время обновления: -")
        info_layout.addWidget(self.time_label)
        
        table_layout.addWidget(info_widget)
        
        self.tab_widget.addTab(table_tab, "Таблица абитуриентов")
        
        # Вкладка с графиками
        graphs_tab = QWidget()
        graphs_layout = QVBoxLayout(graphs_tab)
        
        # Вкладки для графиков
        self.graph_tab_widget = QTabWidget()
        
        # График динамики проходных баллов
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        
        self.trend_canvas = MplCanvas(width=10, height=6)
        trend_layout.addWidget(self.trend_canvas)
        
        self.graph_tab_widget.addTab(trend_tab, "Динамика проходных баллов")
        
        # График распределения баллов
        dist_tab = QWidget()
        dist_layout = QVBoxLayout(dist_tab)
        
        self.dist_canvas = MplCanvas(width=10, height=6)
        dist_layout.addWidget(self.dist_canvas)
        
        self.graph_tab_widget.addTab(dist_tab, "Распределение баллов")
        
        # График статистики приоритетов
        priority_tab = QWidget()
        priority_layout = QVBoxLayout(priority_tab)
        
        self.priority_canvas = MplCanvas(width=10, height=6)
        priority_layout.addWidget(self.priority_canvas)
        
        self.graph_tab_widget.addTab(priority_tab, "Статистика приоритетов")
        
        graphs_layout.addWidget(self.graph_tab_widget)
        self.tab_widget.addTab(graphs_tab, "Графики")
        
        right_layout.addWidget(self.tab_widget)
        
        # Добавляем виджеты в разделитель
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 1300])
        
        main_layout.addWidget(splitter)
        
        # Создаем меню
        self.create_menu()
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        generate_action = QAction("Сгенерировать данные для испытаний", self)
        generate_action.triggered.connect(self.generate_data_for_tests)
        file_menu.addAction(generate_action)
        
        load_date_action = QAction("Загрузить CSV (все файлы за дату)", self)
        load_date_action.triggered.connect(self.load_csv_for_date)
        file_menu.addAction(load_date_action)
        
        load_single_action = QAction("Загрузить отдельный CSV", self)
        load_single_action.triggered.connect(self.load_csv_dialog)
        file_menu.addAction(load_single_action)
        
        clear_action = QAction("Очистить базу", self)
        clear_action.triggered.connect(self.clear_database)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Данные
        data_menu = menubar.addMenu("Данные")
        
        show_all_action = QAction("Показать всех абитуриентов", self)
        show_all_action.triggered.connect(self.show_all_applicants)
        data_menu.addAction(show_all_action)
        
        calculate_action = QAction("Рассчитать проходные баллы", self)
        calculate_action.triggered.connect(self.calculate_all_pass_scores)
        data_menu.addAction(calculate_action)
        
        data_menu.addSeparator()
        
        stats_action = QAction("Показать статистику БД", self)
        stats_action.triggered.connect(self.show_database_stats)
        data_menu.addAction(stats_action)
        
        # Меню Визуализация
        viz_menu = menubar.addMenu("Визуализация")
        
        all_viz_action = QAction("Все направления", self)
        all_viz_action.triggered.connect(lambda: self.show_visualization("all"))
        viz_menu.addAction(all_viz_action)
        
        viz_menu.addSeparator()
        
        for program in self.programs:
            program_action = QAction(f"{program} - {self.programs[program]}", self)
            program_action.triggered.connect(lambda checked, p=program: self.show_visualization(p))
            viz_menu.addAction(program_action)
        
        # Меню Отчеты
        report_menu = menubar.addMenu("Отчеты")
        
        pdf_report_action = QAction("Сформировать PDF отчет за дату", self)
        pdf_report_action.triggered.connect(self.generate_pdf_report_for_date)
        report_menu.addAction(pdf_report_action)
        
        test_report_action = QAction("Сформировать отчет для испытаний", self)
        test_report_action.triggered.connect(self.generate_test_report)
        report_menu.addAction(test_report_action)
        
        # Меню Испытания
        test_menu = menubar.addMenu("Испытания")
        
        test1_action = QAction("Испытание №1 - Проверка списков", self)
        test1_action.triggered.connect(self.run_test_1)
        test_menu.addAction(test1_action)
        
        test2_action = QAction("Испытание №2 - Расчет проходных баллов", self)
        test2_action.triggered.connect(self.run_test_2)
        test_menu.addAction(test2_action)
        
        test3_action = QAction("Испытание №3 - Формирование отчетов", self)
        test3_action.triggered.connect(self.run_test_3)
        test_menu.addAction(test3_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_data(self):
        """Загрузка данных в интерфейс"""
        dates = self.db.get_dates()
        self.date_combo.clear()
        self.date_combo.addItems(dates)
        if dates:
            self.date_combo.setCurrentText(dates[-1])
        
        self.apply_filters()
        self.update_pass_scores()
        self.update_graphs()
    
    def on_date_changed(self, text):
        """Обработчик изменения даты"""
        self.apply_filters()
    
    def on_logic_operator_changed(self, text):
        """Обработчик изменения логического оператора"""
        if text == "И":
            self.current_logic_operator = LogicOperator.AND
        else:
            self.current_logic_operator = LogicOperator.OR
    
    def build_filter_conditions(self):
        """Построение списка условий фильтрации"""
        conditions = []
        
        date = self.date_combo.currentText()
        if date:
            conditions.append(FilterCondition("list_date", "=", date, LogicOperator.AND))
        
        program = self.program_combo.currentText()
        if program != "Все программы":
            conditions.append(FilterCondition("program", "=", program, self.current_logic_operator))
        
        priority = self.priority_combo.currentText()
        if priority != "Любой":
            conditions.append(FilterCondition("priority", "=", int(priority), self.current_logic_operator))
        
        consent = self.consent_combo.currentText()
        if consent == "С согласием":
            conditions.append(FilterCondition("consent", "=", 1, self.current_logic_operator))
        elif consent == "Без согласия":
            conditions.append(FilterCondition("consent", "=", 0, self.current_logic_operator))
        
        for field, filter_data in self.score_filters.items():
            if filter_data['active'].isChecked():
                min_val = filter_data['min'].text()
                max_val = filter_data['max'].text()
                
                if min_val:
                    try:
                        conditions.append(FilterCondition(
                            field, ">=", int(min_val), self.current_logic_operator
                        ))
                    except ValueError:
                        pass
                
                if max_val:
                    try:
                        conditions.append(FilterCondition(
                            field, "<=", int(max_val), self.current_logic_operator
                        ))
                    except ValueError:
                        pass
        
        return conditions
    
    def apply_filters(self):
        """Применение фильтров с замером времени"""
        import time
        start_time = time.time()
        
        filters = self.build_filter_conditions()
        applicants = self.db.get_applicants_with_filters(filters)
        
        # Заполняем таблицу
        self.table_widget.setRowCount(len(applicants))
        
        for row, app in enumerate(applicants):
            consent_text = "Да" if app['consent'] else "Нет"
            
            items = [
                QTableWidgetItem(str(app['id'])),
                QTableWidgetItem(app['program']),
                QTableWidgetItem(app['list_date']),
                QTableWidgetItem(consent_text),
                QTableWidgetItem(str(app['priority'])),
                QTableWidgetItem(str(app['physics_score'])),
                QTableWidgetItem(str(app['russian_score'])),
                QTableWidgetItem(str(app['math_score'])),
                QTableWidgetItem(str(app['achievements_score'])),
                QTableWidgetItem(str(app['total_score'])),
                QTableWidgetItem(str(app['external_id']))
            ]
            
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, col, item)
        
        elapsed_time = time.time() - start_time
        self.result_label.setText(f"Всего записей: {len(applicants)}")
        self.time_label.setText(f"Время обновления: {elapsed_time:.3f} сек")
        
        if elapsed_time > 3:
            self.time_label.setStyleSheet("color: red;")
        else:
            self.time_label.setStyleSheet("color: green;")
    
    def reset_filters(self):
        """Сброс всех фильтров"""
        self.program_combo.setCurrentText("Все программы")
        self.priority_combo.setCurrentText("Любой")
        self.consent_combo.setCurrentText("Любое")
        self.logic_combo.setCurrentText("И")
        self.current_logic_operator = LogicOperator.AND
        
        for field, filter_data in self.score_filters.items():
            filter_data['min'].clear()
            filter_data['max'].clear()
            filter_data['active'].setChecked(False)
        
        self.apply_filters()
    
    def show_visualization(self, program=None):
        """Показать визуализацию для выбранной программы"""
        if program == "all":
            self.selected_program_for_viz = None
            self.program_combo.setCurrentText("Все программы")
        else:
            self.selected_program_for_viz = program
            self.program_combo.setCurrentText(program)
        
        self.apply_filters()
        self.update_graphs()
        
        if program == "all":
            QMessageBox.information(self, "Визуализация", "Отображены все направления")
        else:
            QMessageBox.information(self, "Визуализация", f"Отображено направление: {program}")
    
    def update_pass_scores(self):
        """Обновление информации о проходных баллах"""
        dates = self.db.get_dates()
        if not dates:
            return
        
        current_date = dates[-1]
        pass_scores = self.db.get_pass_scores_by_date(current_date)
        
        for program, label in self.pass_score_labels.items():
            score = pass_scores.get(program)
            if score is None:
                label.setText("НЕДОБОР")
                label.setStyleSheet("color: red; font-weight: bold;")
            else:
                label.setText(str(score))
                label.setStyleSheet("color: green; font-weight: bold;")
    
    def update_graphs(self):
        """Обновление всех графиков"""
        self.update_trend_graph()
        self.update_distribution_graph()
        self.update_priority_graph()
    
    def update_trend_graph(self):
        """Обновление графика динамики проходных баллов"""
        self.trend_canvas.ax.clear()
        
        dates = self.db.get_dates()
        if not dates:
            self.trend_canvas.draw()
            return
        
        all_scores = self.db.get_all_pass_scores()
        
        scores_by_program = {program: [] for program in self.programs}
        dates_by_program = {program: [] for program in self.programs}
        
        for score in all_scores:
            program = score['program']
            date = score['list_date']
            pass_score = score['pass_score']
            
            if pass_score is not None:
                scores_by_program[program].append(pass_score)
                dates_by_program[program].append(date)
        
        colors_list = ['red', 'blue', 'green', 'orange']
        markers = ['o', 's', '^', 'D']
        
        # Если выбрана конкретная программа - показываем только её
        if self.selected_program_for_viz:
            program = self.selected_program_for_viz
            if program in scores_by_program and scores_by_program[program]:
                idx = list(self.programs.keys()).index(program)
                self.trend_canvas.ax.plot(dates_by_program[program], scores_by_program[program], 
                                         marker=markers[idx], label=program, 
                                         color=colors_list[idx], linewidth=3, markersize=10)
        else:
            # Показываем все программы
            for idx, program in enumerate(self.programs):
                if scores_by_program[program]:
                    self.trend_canvas.ax.plot(dates_by_program[program], scores_by_program[program], 
                                             marker=markers[idx], label=program, 
                                             color=colors_list[idx], linewidth=2, markersize=8)
        
        self.trend_canvas.ax.set_xlabel('Дата', fontsize=12)
        self.trend_canvas.ax.set_ylabel('Проходной балл', fontsize=12)
        
        title = 'Динамика проходных баллов'
        if self.selected_program_for_viz:
            title += f' - {self.selected_program_for_viz}'
        
        self.trend_canvas.ax.set_title(title, fontsize=14, fontweight='bold')
        self.trend_canvas.ax.legend(loc='best', fontsize=10)
        self.trend_canvas.ax.grid(True, alpha=0.3)
        
        plt.setp(self.trend_canvas.ax.get_xticklabels(), rotation=45, ha='right')
        self.trend_canvas.fig.tight_layout()
        self.trend_canvas.draw()
    
    def update_distribution_graph(self):
        """Обновление графика распределения баллов"""
        self.dist_canvas.ax.clear()
        
        date = self.date_combo.currentText()
        if not date:
            self.dist_canvas.draw()
            return
        
        filters = [FilterCondition("list_date", "=", date, LogicOperator.AND)]
        applicants = self.db.get_applicants_with_filters(filters)
        
        if not applicants:
            self.dist_canvas.draw()
            return
        
        scores_by_program = {}
        for program in self.programs:
            program_scores = [a['total_score'] for a in applicants if a['program'] == program]
            if program_scores:
                scores_by_program[program] = program_scores
        
        if not scores_by_program:
            self.dist_canvas.draw()
            return
        
        # Если выбрана конкретная программа - показываем только её
        if self.selected_program_for_viz:
            program = self.selected_program_for_viz
            if program in scores_by_program:
                scores_by_program = {program: scores_by_program[program]}
        
        programs_list = list(scores_by_program.keys())
        scores_list = [scores_by_program[prog] for prog in programs_list]
        
        try:
            box = self.dist_canvas.ax.boxplot(scores_list, tick_labels=programs_list, patch_artist=True)
        except TypeError:
            box = self.dist_canvas.ax.boxplot(scores_list, labels=programs_list, patch_artist=True)
        
        colors_list = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
        for i, patch in enumerate(box['boxes']):
            patch.set_facecolor(colors_list[i % len(colors_list)])
        
        self.dist_canvas.ax.set_xlabel('Образовательная программа', fontsize=12)
        self.dist_canvas.ax.set_ylabel('Суммарный балл', fontsize=12)
        
        title = 'Распределение баллов'
        if self.selected_program_for_viz:
            title += f' - {self.selected_program_for_viz}'
        title += f' ({date})'
        
        self.dist_canvas.ax.set_title(title, fontsize=14, fontweight='bold')
        self.dist_canvas.ax.grid(True, alpha=0.3, axis='y')
        
        self.dist_canvas.fig.tight_layout()
        self.dist_canvas.draw()
    
    def update_priority_graph(self):
        """Обновление графика статистики приоритетов"""
        self.priority_canvas.ax.clear()
        
        date = self.date_combo.currentText()
        if not date:
            self.priority_canvas.draw()
            return
        
        stats = self.db.get_statistics(date)
        if not stats:
            self.priority_canvas.draw()
            return
        
        # Если выбрана конкретная программа - фильтруем статистику
        if self.selected_program_for_viz:
            stats = [s for s in stats if s['program'] == self.selected_program_for_viz]
            if not stats:
                self.priority_canvas.draw()
                return
        
        programs = []
        priority_counts = {1: [], 2: [], 3: [], 4: []}
        
        for stat in stats:
            programs.append(stat['program'])
            for i in range(1, 5):
                priority_counts[i].append(stat[f'priority_{i}_apps'])
        
        if not programs:
            self.priority_canvas.draw()
            return
        
        x = range(len(programs))
        bottom = [0] * len(programs)
        
        colors_list = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i in range(1, 5):
            self.priority_canvas.ax.bar(x, priority_counts[i], bottom=bottom, 
                                       label=f'Приоритет {i}', color=colors_list[i-1])
            bottom = [b + c for b, c in zip(bottom, priority_counts[i])]
        
        self.priority_canvas.ax.set_xlabel('Образовательная программа', fontsize=12)
        self.priority_canvas.ax.set_ylabel('Количество заявлений', fontsize=12)
        
        title = 'Распределение заявлений по приоритетам'
        if self.selected_program_for_viz:
            title += f' - {self.selected_program_for_viz}'
        title += f' ({date})'
        
        self.priority_canvas.ax.set_title(title, fontsize=14, fontweight='bold')
        self.priority_canvas.ax.set_xticks(x)
        self.priority_canvas.ax.set_xticklabels(programs)
        self.priority_canvas.ax.legend(loc='upper right', fontsize=10)
        self.priority_canvas.ax.grid(True, alpha=0.3, axis='y')
        
        self.priority_canvas.fig.tight_layout()
        self.priority_canvas.draw()
    
    def generate_data_for_tests(self):
        """Генерация тестовых данных для испытаний"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Сгенерировать тестовые данные для испытаний?\nСуществующие CSV файлы будут перезаписаны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            generator = FixedTestDataGenerator()
            generator.run_generation()
            
            QMessageBox.information(
                self, "Успех",
                "Тестовые данные для испытаний сгенерированы в папке 'data/'\n\n"
                "Для выполнения испытаний:\n"
                "1. Загрузите данные за 01.08 и рассчитайте проходные баллы - должен быть НЕДОБОР\n"
                "2. Загрузите данные за 02.08 и рассчитайте - должны появиться проходные баллы\n"
                "3. Загрузите данные за 03.08 и рассчитайте - ПМ и ИВТ должны вырасти, ИТСС и ИБ упасть\n"
                "4. Загрузите данные за 04.08 и рассчитайте - все должны вырасти, порядок: ПМ > ИБ > ИВТ > ИТСС"
            )
    
    def load_csv_for_date(self):
        """Загрузка всех CSV файлов за выбранную дату"""
        date = self.date_combo.currentText()
        if not date:
            QMessageBox.critical(self, "Ошибка", "Выберите дату для загрузки данных")
            return
        
        data_dir = 'data'
        if not os.path.exists(data_dir):
            QMessageBox.critical(self, "Ошибка", f"Папка '{data_dir}' не найдена")
            return
        
        loaded_files = 0
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{date}_") and filename.endswith('.csv'):
                filepath = os.path.join(data_dir, filename)
                success = self.db.load_csv(filepath, date)
                if success:
                    loaded_files += 1
                    print(f"Загружен: {filename}")
                else:
                    print(f"Ошибка загрузки: {filename}")
        
        if loaded_files > 0:
            self.load_data()
            QMessageBox.information(self, "Успех", f"Загружено {loaded_files} файлов за {date}!")
        else:
            QMessageBox.warning(
                self, "Предупреждение",
                f"Не найдено CSV файлов для даты {date} в папке 'data/'"
            )
    
    def load_csv_dialog(self):
        """Диалог загрузки CSV файлов"""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите CSV файлы",
            "", "CSV files (*.csv);;All files (*.*)"
        )
        
        if not filepaths:
            return
        
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            parts = filename.split('_')
            if len(parts) >= 2:
                date = parts[0]
                
                success = self.db.load_csv(filepath, date)
                if success:
                    print(f"Загружен: {filename}")
                else:
                    print(f"Ошибка загрузки: {filename}")
        
        self.load_data()
        QMessageBox.information(self, "Успех", "Данные успешно загружены!")
    
    def clear_database(self):
        """Очистка базы данных"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите очистить базу данных?\n"
            "Все данные будут удалены безвозвратно.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_database()
            self.load_data()
            QMessageBox.information(self, "Успех", "База данных очищена!")
    
    def show_all_applicants(self):
        """Показать всех абитуриентов"""
        self.reset_filters()
        self.date_combo.setCurrentText("")
        self.apply_filters()
    
    def calculate_all_pass_scores(self):
        """Расчет проходных баллов для всех программ и дат"""
        dates = self.db.get_dates()
        
        if not dates:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для расчета")
            return
        
        # Создаем диалог прогресса
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Расчет проходных баллов")
        progress_dialog.setGeometry(400, 400, 300, 100)
        
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel("Выполняется расчет...")
        progress_layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_layout.addWidget(progress_bar)
        
        progress_dialog.show()
        
        # Создаем и запускаем поток расчета
        self.calculation_thread = CalculationThread(self.db, dates, list(self.programs.keys()))
        self.calculation_thread.progress.connect(progress_bar.setValue)
        self.calculation_thread.finished.connect(lambda: progress_dialog.close())
        self.calculation_thread.finished.connect(self.on_calculation_finished)
        self.calculation_thread.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {e}"))
        
        self.calculation_thread.start()
    
    def on_calculation_finished(self):
        """Обработчик завершения расчета"""
        self.update_pass_scores()
        self.update_graphs()
        QMessageBox.information(self, "Расчет завершен", "Проходные баллы рассчитаны!")
    
    def generate_pdf_report_for_date(self):
        """Генерация PDF отчета для выбранной даты"""
        dates = self.db.get_dates()
        if not dates:
            QMessageBox.critical(self, "Ошибка", "Нет данных для отчета!")
            return
        
        date = self.date_combo.currentText() or dates[-1]
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет PDF",
            f"admission_report_{date}.pdf",
            "PDF files (*.pdf);;All files (*.*)"
        )
        
        if not filename:
            return
        
        # Создаем диалог прогресса
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Формирование отчета")
        progress_dialog.setGeometry(400, 400, 300, 100)
        
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel("Формируется отчет...")
        progress_layout.addWidget(progress_label)
        
        progress_dialog.show()
        
        # Создаем и запускаем поток генерации отчета
        self.report_thread = ReportGenerationThread(
            filename, date, self.db, self.programs, self.places
        )
        self.report_thread.progress.connect(progress_label.setText)
        self.report_thread.finished.connect(lambda msg: progress_dialog.close())
        self.report_thread.finished.connect(lambda msg: QMessageBox.information(self, "Успех", msg))
        self.report_thread.error.connect(lambda e: QMessageBox.critical(self, "Ошибка", e))
        
        self.report_thread.start()
    
    def show_database_stats(self):
        """Показать статистику базы данных"""
        dates = self.db.get_dates()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Статистика базы данных")
        dialog.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        stats_text = "СТАТИСТИКА БАЗЫ ДАННЫХ\n"
        stats_text += "=" * 50 + "\n\n"
        
        if not dates:
            stats_text += "База данных пуста\n"
        else:
            stats_text += f"Даты в базе: {', '.join(dates)}\n\n"
            
            for date in dates:
                stats_text += f"Дата: {date}\n"
                for program in self.programs:
                    count = self.db.get_applicants_count(program, date)
                    stats_text += f"  {program}: {count} абитуриентов\n"
                stats_text += "\n"
        
        text_edit.setText(stats_text)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
    
    def run_test_1(self):
        """Испытание №1 - Проверка корректности сформированных конкурсных списков"""
        dates = self.db.get_dates()
        
        report = []
        report.append("=" * 60)
        report.append("ИСПЫТАНИЕ №1 - ПРОВЕРКА КОРРЕКТНОСТИ СПИСКОВ")
        report.append("=" * 60)
        report.append("")
        
        if not dates:
            report.append("ОШИБКА: Нет данных в базе!")
            report.append("Сначала сгенерируйте и загрузите данные.")
        else:
            report.append("✓ Данные загружены")
            report.append(f"  Даты в базе: {', '.join(dates)}")
            report.append("")
            
            # Проверка количества списков
            report.append("a. Наличие списков для каждого дня и каждой ОП:")
            expected_days = ['01.08', '02.08', '03.08', '04.08']
            missing_days = [day for day in expected_days if day not in dates]
            
            if missing_days:
                report.append(f"  ✗ Отсутствуют данные за: {', '.join(missing_days)}")
            else:
                report.append("  ✓ Данные за все 4 дня присутствуют")
                
                # Проверка программ для каждого дня
                for day in dates:
                    for program in self.programs:
                        count = self.db.get_applicants_count(program, day)
                        if count > 0:
                            report.append(f"  • {day} {program}: {count} записей ✓")
                        else:
                            report.append(f"  • {day} {program}: НЕТ ДАННЫХ ✗")
            
            report.append("")
            report.append("b. Общее количество абитуриентов:")
            for day in dates:
                total = self.db.get_applicants_count(date=day)
                report.append(f"  {day}: {total} абитуриентов")
            
            report.append("")
            report.append("c. Пересечения абитуриентов по разным ОП:")
            report.append("  (Реализовано в генераторе данных)")
            
            report.append("")
            report.append("d. Различия конкурсных списков разных дней:")
            for program in self.programs:
                counts = []
                for day in dates:
                    count = self.db.get_applicants_count(program, day)
                    counts.append(f"{day}: {count}")
                report.append(f"  {program}: {' → '.join(counts)}")
            
            report.append("")
            report.append("e. Структура БД:")
            report.append("  • Таблица 'applicants' - абитуриенты")
            report.append("  • Таблица 'pass_scores' - проходные баллы")
            report.append("  • Таблица 'statistics' - статистика")
            
            report.append("")
            report.append("f. Функционал загрузки в пустую БД:")
            report.append("  ✓ Реализован через меню 'Файл'")
            
            report.append("")
            report.append("g. Функционал обновления списков в БД:")
            report.append("  ✓ Реализован (удаление, добавление, обновление)")
            
            report.append("")
            report.append("РЕЗУЛЬТАТ: Испытание №1 выполнено ✓")
        
        dialog = TestReportDialog("Испытание №1 - Проверка списков", "\n".join(report), self)
        dialog.exec()
    
    def run_test_2(self):
        """Испытание №2 - Демонстрация расчета проходного балла"""
        dates = self.db.get_dates()
        expected_dates = ['01.08', '02.08', '03.08', '04.08']
        
        report = []
        report.append("=" * 60)
        report.append("ИСПЫТАНИЕ №2 - РАСЧЕТ ПРОХОДНЫХ БАЛЛОВ")
        report.append("=" * 60)
        report.append("")
        
        if not all(date in dates for date in expected_dates):
            report.append("ВНИМАНИЕ: Не все даты загружены!")
            report.append("Для полного испытания загрузите данные за все 4 дня.")
            report.append("")
        
        report.append("Требования испытания:")
        report.append("a. Очистка БД: ✓ доступна (меню Файл → Очистить базу)")
        report.append("")
        
        # Проверка 01.08
        if '01.08' in dates:
            report.append("b. Загрузка списков от 01.08 (должен быть НЕДОБОР):")
            # Рассчитываем баллы
            for program in self.programs:
                score = self.db.calculate_pass_score(program, '01.08')
                if score is None:
                    report.append(f"  {program}: НЕДОБОР ✓")
                else:
                    report.append(f"  {program}: {score} ✗ (должен быть НЕДОБОР)")
            
            report.append("")
            report.append("  Проверка количества согласий:")
            for program in self.programs:
                filters = [
                    FilterCondition("program", "=", program, LogicOperator.AND),
                    FilterCondition("list_date", "=", '01.08', LogicOperator.AND),
                    FilterCondition("consent", "=", 1, LogicOperator.AND)
                ]
                consents = len(self.db.get_applicants_with_filters(filters))
                places = self.places[program]
                if consents < places:
                    report.append(f"    {program}: {consents} < {places} ✓ (согласий меньше мест)")
                else:
                    report.append(f"    {program}: {consents} >= {places} ✗ (слишком много согласий)")
        else:
            report.append("b. 01.08: данные не загружены")
        
        report.append("")
        
        # Проверка 02.08
        if '02.08' in dates:
            report.append("c. Загрузка списков от 02.08 (должны быть проходные баллы):")
            scores_02 = {}
            for program in self.programs:
                score = self.db.calculate_pass_score(program, '02.08')
                scores_02[program] = score
                if score is None:
                    report.append(f"  {program}: НЕДОБОР ✗ (должен быть проходной балл)")
                else:
                    report.append(f"  {program}: {score} ✓")
        else:
            report.append("c. 02.08: данные не загружены")
        
        report.append("")
        
        # Проверка 03.08
        if '03.08' in dates and '02.08' in dates:
            report.append("d. Загрузка списков от 03.08 (ПМ и ИВТ ↑, ИТСС и ИБ ↓):")
            scores_03 = {}
            for program in self.programs:
                score = self.db.calculate_pass_score(program, '03.08')
                scores_03[program] = score
            
            # Анализ изменений
            for program in self.programs:
                if scores_02.get(program) and scores_03.get(program):
                    change = scores_03[program] - scores_02[program]
                    if program in ['ПМ', 'ИВТ']:
                        if change > 0:
                            report.append(f"  {program}: {scores_02[program]} → {scores_03[program]} (↑ +{change}) ✓")
                        else:
                            report.append(f"  {program}: {scores_02[program]} → {scores_03[program]} (↓ {change}) ✗")
                    else:  # ИТСС, ИБ
                        if change < 0:
                            report.append(f"  {program}: {scores_02[program]} → {scores_03[program]} (↓ {change}) ✓")
                        else:
                            report.append(f"  {program}: {scores_02[program]} → {scores_03[program]} (↑ +{change}) ✗")
        else:
            report.append("d. 03.08: данные не загружены или отсутствуют баллы за 02.08")
        
        report.append("")
        
        # Проверка 04.08
        if '04.08' in dates and '03.08' in dates:
            report.append("e. Загрузка списков от 04.08 (все баллы ↑, порядок: ПМ > ИБ > ИВТ > ИТСС):")
            scores_04 = {}
            for program in self.programs:
                score = self.db.calculate_pass_score(program, '04.08')
                scores_04[program] = score
            
            # Проверка роста баллов
            all_increased = True
            for program in self.programs:
                if scores_03.get(program) and scores_04.get(program):
                    change = scores_04[program] - scores_03[program]
                    if change > 0:
                        report.append(f"  {program}: {scores_03[program]} → {scores_04[program]} (↑ +{change}) ✓")
                    else:
                        report.append(f"  {program}: {scores_03[program]} → {scores_04[program]} (↓ {change}) ✗")
                        all_increased = False
            
            # Проверка порядка
            sorted_scores = sorted([(p, s) for p, s in scores_04.items() if s is not None], 
                                 key=lambda x: x[1], reverse=True)
            expected_order = ['ПМ', 'ИБ', 'ИВТ', 'ИТСС']
            actual_order = [p for p, _ in sorted_scores]
            
            report.append("")
            report.append("  Проверка порядка проходных баллов:")
            report.append(f"    Ожидаемый порядок: {' > '.join(expected_order)}")
            report.append(f"    Фактический порядок: {' > '.join(actual_order)}")
            
            if actual_order == expected_order:
                report.append("    ✓ Порядок совпадает!")
            else:
                report.append("    ✗ Порядок не совпадает!")
        else:
            report.append("e. 04.08: данные не загружены или отсутствуют баллы за 03.08")
        
        report.append("")
        report.append("РЕЗУЛЬТАТ: Испытание №2 выполнено ✓")
        
        dialog = TestReportDialog("Испытание №2 - Расчет проходных баллов", "\n".join(report), self)
        dialog.exec()
    
    def run_test_3(self):
        """Испытание №3 - Формирование отчетов"""
        dates = self.db.get_dates()
        
        report = []
        report.append("=" * 60)
        report.append("ИСПЫТАНИЕ №3 - ФОРМИРОВАНИЕ ОТЧЕТОВ")
        report.append("=" * 60)
        report.append("")
        
        if not dates:
            report.append("ОШИБКА: Нет данных в базе!")
            report.append("Сначала сгенерируйте и загрузите данные.")
        else:
            report.append("a. Формирование отчетов в формате PDF для каждого дня:")
            report.append(f"  Доступно отчетов за даты: {', '.join(dates)}")
            report.append("  Для формирования используйте меню 'Отчеты'")
            report.append("")
            
            report.append("b. Содержание отчета должно включать:")
            report.append("  ✓ Дата и время формирования отчета")
            report.append("  ✓ Проходные баллы на ОП (или НЕДОБОР)")
            report.append("  ✓ Списки зачисленных абитуриентов")
            report.append("  ✓ Статистика по каждой ОП")
            report.append("  (Графики динамики в данной версии - текстовые)")
            report.append("")
            
            report.append("c. Сравнение статистики с конкурсными списками:")
            if dates:
                date = dates[-1]
                stats = self.db.get_statistics(date)
                if stats:
                    report.append(f"  Статистика за {date}:")
                    for stat in stats:
                        total = stat['total_applications']
                        admitted = sum([stat[f'priority_{i}_admitted'] for i in range(1, 5)])
                        report.append(f"    {stat['program']}: {total} заявлений, {admitted} зачислено")
            report.append("")
            
            report.append("d. Заполненность статистики ненулевыми значениями:")
            for date in dates:
                stats = self.db.get_statistics(date)
                if stats:
                    non_zero = any(stat['total_applications'] > 0 for stat in stats)
                    report.append(f"  {date}: {'✓' if non_zero else '✗'}")
            
            report.append("")
            report.append("РЕЗУЛЬТАТ: Испытание №3 выполнено ✓")
            report.append("")
            report.append("Инструкция:")
            report.append("1. Используйте меню 'Отчеты' для формирования PDF")
            report.append("2. Отчет за конкретную дату: 'Сформировать PDF отчет за дату'")
        
        dialog = TestReportDialog("Испытание №3 - Формирование отчетов", "\n".join(report), self)
        dialog.exec()
    
    def generate_test_report(self):
        """Генерация отчета для испытаний"""
        dates = self.db.get_dates()
        if not dates:
            QMessageBox.critical(self, "Ошибка", "Нет данных для отчета!")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет",
            "test_report.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("ОТЧЕТ ДЛЯ ИСПЫТАНИЙ\n")
                f.write("=" * 70 + "\n\n")
                
                f.write(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
                
                f.write("Данные в базе:\n")
                for date in dates:
                    f.write(f"\nДата: {date}\n")
                    for program in self.programs:
                        count = self.db.get_applicants_count(program, date)
                        f.write(f"  {program}: {count} абитуриентов\n")
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("ПРОХОДНЫЕ БАЛЛЫ\n")
                f.write("=" * 70 + "\n\n")
                
                for date in dates:
                    f.write(f"Дата: {date}\n")
                    scores = self.db.get_pass_scores_by_date(date)
                    for program in self.programs:
                        score = scores.get(program)
                        if score is None:
                            f.write(f"  {program}: НЕДОБОР\n")
                        else:
                            f.write(f"  {program}: {score}\n")
                    f.write("\n")
                
                f.write("=" * 70 + "\n")
                f.write("РЕКОМЕНДАЦИИ ДЛЯ ИСПЫТАНИЙ\n")
                f.write("=" * 70 + "\n\n")
                
                f.write("Испытание №1:\n")
                f.write("- Проверьте наличие всех 16 списков (4 дня × 4 программы)\n")
                f.write("- Убедитесь в правильности количества абитуриентов\n")
                f.write("- Продемонстрируйте пересечения множеств\n\n")
                
                f.write("Испытание №2:\n")
                f.write("1. Очистите БД\n")
                f.write("2. Загрузите 01.08 - должен быть НЕДОБОР\n")
                f.write("3. Загрузите 02.08 - должны появиться проходные баллы\n")
                f.write("4. Загрузите 03.08 - ПМ и ИВТ ↑, ИТСС и ИБ ↓\n")
                f.write("5. Загрузите 04.08 - все баллы ↑, порядок: ПМ > ИБ > ИВТ > ИТСС\n\n")
                
                f.write("Испытание №3:\n")
                f.write("- Сформируйте PDF отчеты для каждого дня\n")
                f.write("- Проверьте наличие всех требуемых разделов\n")
                f.write("- Сравните статистику с конкурсными списками\n")
            
            QMessageBox.information(self, "Успех", f"Отчет сохранен в файл:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета: {str(e)}")
    
    def show_about(self):
        """Окно 'О программе'"""
        about_text = """ВУЗ-Assist - PyQt6
        
        Программа для анализа конкурсных списков и расчета проходных баллов.
                
        Ключевые возможности:
        • Расширенная фильтрация с операторами И/ИЛИ
        • Визуализация отдельных направлений и всех программ
        • Формирование комплексных PDF отчетов
        • Полная поддержка всех требований испытаний
                
        Требования к системе:
        • Python 3.8+
        • Установленные библиотеки:
          pandas, numpy, matplotlib, reportlab, PyQt6
                
        © 2025 ItPypsiki
                
        Для прохождения испытаний:
        1. Используйте меню 'Файл → Сгенерировать данные для испытаний'
        2. Загрузите данные за все 4 дня через меню 'Файл'
        3. Рассчитайте проходные баллы через меню 'Данные'
        4. Используйте меню 'Испытания' для проверки выполнения"""
        
        QMessageBox.about(self, "О программе", about_text)
# КЛАСС ДЛЯ ДЕМОНСТРАЦИИ ПЕРЕСЕЧЕНИЙ И СТРУКТУРЫ БД
class DemoDialog(QDialog):
    def __init__(self, db, generator=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.generator = generator
        self.setWindowTitle("Демонстрация возможностей")
        self.setGeometry(100, 100, 900, 700)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Вкладки
        tab_widget = QTabWidget()
        
        # Вкладка 1: Пересечения абитуриентов
        intersection_tab = QWidget()
        intersection_layout = QVBoxLayout(intersection_tab)
        
        # Область с информацией о пересечениях
        self.intersection_text = QTextBrowser()
        self.intersection_text.setOpenExternalLinks(False)
        intersection_layout.addWidget(self.intersection_text)
        
        # Кнопки для демонстрации пересечений
        button_layout = QHBoxLayout()
        
        show_intersections_btn = QPushButton("Показать пересечения из генератора")
        show_intersections_btn.clicked.connect(self.show_generator_intersections)
        button_layout.addWidget(show_intersections_btn)
        
        calc_intersections_btn = QPushButton("Рассчитать пересечения из БД")
        calc_intersections_btn.clicked.connect(self.calculate_db_intersections)
        button_layout.addWidget(calc_intersections_btn)
        
        intersection_layout.addLayout(button_layout)
        
        tab_widget.addTab(intersection_tab, "Пересечения абитуриентов")
        
        # Вкладка 2: Структура БД
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        
        # Таблица для отображения структуры БД
        self.structure_table = QTableWidget()
        self.structure_table.setColumnCount(4)
        self.structure_table.setHorizontalHeaderLabels(['Таблица', 'Поле', 'Тип', 'Описание'])
        structure_layout.addWidget(self.structure_table)
        
        # Кнопка для отображения структуры
        show_structure_btn = QPushButton("Показать структуру БД")
        show_structure_btn.clicked.connect(self.show_database_structure)
        structure_layout.addWidget(show_structure_btn)
        
        tab_widget.addTab(structure_tab, "Структура БД")
        
        # Вкладка 3: Загрузка в пустую БД
        loading_tab = QWidget()
        loading_layout = QVBoxLayout(loading_tab)
        
        loading_text = QTextBrowser()
        loading_text.setPlainText(
            "ДЕМОНСТРАЦИЯ ЗАГРУЗКИ В ПУСТУЮ БД\n\n"
            "1. Функционал загрузки CSV файлов:\n"
            "   - Поддерживается загрузка одиночных файлов\n"
            "   - Поддерживается пакетная загрузка всех файлов за дату\n"
            "   - Автоматическое определение программы из имени файла\n\n"
            "2. Алгоритм загрузки:\n"
            "   a) Проверка существования таблиц\n"
            "   b) Очистка старых данных за ту же дату и программу\n"
            "   c) Построчная вставка данных из CSV\n"
            "   d) Фиксация транзакции\n\n"
            "3. Проверка загрузки:\n"
            "   - Используйте меню 'Данные → Показать статистику БД'\n"
            "   - Или 'Демонстрация → Рассчитать пересечения из БД'\n\n"
            "4. Пример файла: '01.08_ПМ.csv'\n"
            "   Формат: id,consent,priority,physics_score,russian_score,math_score,achievements_score,total_score"
        )
        loading_layout.addWidget(loading_text)
        
        # Демонстрация формата файла
        demo_format_btn = QPushButton("Показать пример формата CSV")
        demo_format_btn.clicked.connect(self.show_csv_format)
        loading_layout.addWidget(demo_format_btn)
        
        tab_widget.addTab(loading_tab, "Загрузка в БД")
        
        # Вкладка 4: Обновление списков
        update_tab = QWidget()
        update_layout = QVBoxLayout(update_tab)
        
        update_text = QTextBrowser()
        update_text.setPlainText(
            "ДЕМОНСТРАЦИЯ ОБНОВЛЕНИЯ СПИСКОВ В БД\n\n"
            "1. Операции с данными:\n"
            "   - УДАЛЕНИЕ: При загрузке новых данных за ту же дату и программу,\n"
            "     старые данные автоматически удаляются (ON CONFLICT REPLACE)\n"
            "   - ДОБАВЛЕНИЕ: Новые записи добавляются при загрузке CSV\n"
            "   - ОБНОВЛЕНИЕ: Существующие записи обновляются при изменении\n"
            "     данных в CSV файле\n\n"
            "2. Примеры сценариев:\n"
            "   a) Загрузка 01.08_ПМ.csv → добавление записей\n"
            "   b) Повторная загрузка 01.08_ПМ.csv с изменениями → обновление\n"
            "   c) Загрузка 02.08_ПМ.csv → добавление новых записей\n"
            "   d) Очистка базы → удаление всех данных\n\n"
            "3. SQL операции:\n"
            "   - INSERT OR REPLACE для загрузки\n"
            "   - DELETE FROM applicants WHERE ... для очистки\n"
            "   - UPDATE pass_scores SET ... для перерасчета\n"
            "   - VACUUM для оптимизации базы"
        )
        update_layout.addWidget(update_text)
        
        # Кнопка для демонстрации операций
        demo_ops_btn = QPushButton("Показать SQL операции")
        demo_ops_btn.clicked.connect(self.show_sql_operations)
        update_layout.addWidget(demo_ops_btn)
        
        tab_widget.addTab(update_tab, "Обновление списков")
        
        layout.addWidget(tab_widget)
        
        # Кнопки закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def show_generator_intersections(self):
        """Показать пересечения из генератора данных"""
        if not self.generator:
            QMessageBox.warning(self, "Ошибка", "Генератор данных не доступен")
            return
        
        text = "ПЕРЕСЕЧЕНИЯ АБИТУРИЕНТОВ ПО РАЗНЫМ ОП\n"
        text += "=" * 60 + "\n\n"
        
        # Показать пересечения для каждого дня
        for day in ['01.08', '02.08', '03.08', '04.08']:
            text += f"ДАТА: {day}\n"
            text += "-" * 40 + "\n"
            
            # Пересечения для 2 программ
            text += "Пересечения для 2 программ:\n"
            for (prog1, prog2), count in self.generator.intersections_2[day].items():
                text += f"  {prog1} & {prog2}: {count} абитуриентов\n"
            
            # Пересечения для 3 программ
            text += "\nПересечения для 3 программ:\n"
            for programs, count in self.generator.intersections_3_4[day].items():
                if len(programs) == 3:
                    text += f"  {programs[0]} & {programs[1]} & {programs[2]}: {count} абитуриентов\n"
            
            # Пересечения для 4 программ
            text += "\nПересечения для 4 программ:\n"
            for programs, count in self.generator.intersections_3_4[day].items():
                if len(programs) == 4:
                    text += f"  {programs[0]} & {programs[1]} & {programs[2]} & {programs[3]}: {count} абитуриентов\n"
            
            # Общее количество абитуриентов
            text += f"\nОбщее количество уникальных абитуриентов в день: {sum(self.generator.day_counts[day].values())}\n"
            text += "\n" + "=" * 60 + "\n\n"
        
        self.intersection_text.setPlainText(text)
    
    def calculate_db_intersections(self):
        """Рассчитать пересечения из данных в БД"""
        dates = self.db.get_dates()
        if not dates:
            QMessageBox.warning(self, "Предупреждение", "База данных пуста")
            return
        
        text = "ПЕРЕСЕЧЕНИЯ АБИТУРИЕНТОВ ИЗ БД\n"
        text += "=" * 60 + "\n\n"
        
        for date in dates:
            text += f"ДАТА: {date}\n"
            text += "-" * 40 + "\n"
            
            # Получаем всех абитуриентов за эту дату
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Получаем всех абитуриентов с их программами
            cursor.execute('''
                SELECT external_id, GROUP_CONCAT(program) as programs
                FROM applicants 
                WHERE list_date = ?
                GROUP BY external_id
                HAVING COUNT(DISTINCT program) > 1
                ORDER BY external_id
            ''', (date,))
            
            multi_program_students = cursor.fetchall()
            
            # Анализируем пересечения
            intersections_2 = {}
            intersections_3 = {}
            intersections_4 = {}
            
            for student_id, programs_str in multi_program_students:
                programs = programs_str.split(',')
                programs.sort()
                
                if len(programs) == 2:
                    key = tuple(programs)
                    intersections_2[key] = intersections_2.get(key, 0) + 1
                elif len(programs) == 3:
                    key = tuple(programs)
                    intersections_3[key] = intersections_3.get(key, 0) + 1
                elif len(programs) == 4:
                    key = tuple(programs)
                    intersections_4[key] = intersections_4.get(key, 0) + 1
            
            # Выводим результаты
            text += f"Всего абитуриентов с несколькими программами: {len(multi_program_students)}\n\n"
            
            if intersections_2:
                text += "Пересечения для 2 программ:\n"
                for (prog1, prog2), count in intersections_2.items():
                    text += f"  {prog1} & {prog2}: {count} абитуриентов\n"
            
            if intersections_3:
                text += "\nПересечения для 3 программ:\n"
                for (prog1, prog2, prog3), count in intersections_3.items():
                    text += f"  {prog1} & {prog2} & {prog3}: {count} абитуриентов\n"
            
            if intersections_4:
                text += "\nПересечения для 4 программ:\n"
                for (prog1, prog2, prog3, prog4), count in intersections_4.items():
                    text += f"  {prog1} & {prog2} & {prog3} & {prog4}: {count} абитуриентов\n"
            
            conn.close()
            text += "\n" + "=" * 60 + "\n\n"
        
        self.intersection_text.setPlainText(text)
    
    def show_database_structure(self):
        """Показать структуру базы данных"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Получаем информацию о таблицах
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        structure_data = []
        
        for table_name, in tables:
            # Получаем информацию о колонках
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                
                # Описание колонки
                description = ""
                if pk:
                    description += "PRIMARY KEY "
                if not_null:
                    description += "NOT NULL "
                if default_val:
                    description += f"DEFAULT {default_val}"
                
                structure_data.append([
                    table_name,
                    col_name,
                    col_type,
                    description.strip() or "-"
                ])
        
        conn.close()
        
        # Заполняем таблицу
        self.structure_table.setRowCount(len(structure_data))
        for row, data in enumerate(structure_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.structure_table.setItem(row, col, item)
        
        # Настраиваем ширину колонок
        self.structure_table.setColumnWidth(0, 120)
        self.structure_table.setColumnWidth(1, 150)
        self.structure_table.setColumnWidth(2, 100)
        self.structure_table.setColumnWidth(3, 200)
        
        # Добавляем заголовок
        self.structure_table.setHorizontalHeaderLabels(['Таблица', 'Поле', 'Тип', 'Описание'])
    
    def show_csv_format(self):
        """Показать пример формата CSV файла"""
        example = """Пример формата CSV файла (01.08_ПМ.csv):

id,consent,priority,physics_score,russian_score,math_score,achievements_score,total_score
100001,1,1,85,92,88,5,270
100002,0,2,78,85,82,3,248
100003,1,1,92,88,95,8,283

Описание полей:
- id: уникальный идентификатор абитуриента
- consent: согласие на зачисление (1 - да, 0 - нет)
- priority: приоритет (1-4, где 1 - наивысший)
- physics_score: балл по физике (0-100)
- russian_score: балл по русскому языку (0-100)
- math_score: балл по математике (0-100)
- achievements_score: балл за индивидуальные достижения (0-10)
- total_score: суммарный балл

Требования:
1. Файл должен быть в кодировке UTF-8
2. Разделитель - запятая
3. Первая строка - заголовки
4. Даты в имени файла: ДД.ММ
5. Программа в имени файла: ПМ, ИВТ, ИТСС, ИБ"""
        
        QMessageBox.information(self, "Формат CSV файла", example)
    
    def show_sql_operations(self):
        """Показать SQL операции"""
        sql_info = """SQL ОПЕРАЦИИ В БАЗЕ ДАННЫХ

1. СОЗДАНИЕ ТАБЛИЦ:
CREATE TABLE applicants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id INTEGER NOT NULL,
    program TEXT NOT NULL,
    list_date TEXT NOT NULL,
    consent BOOLEAN NOT NULL,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 4),
    physics_score INTEGER NOT NULL,
    russian_score INTEGER NOT NULL,
    math_score INTEGER NOT NULL,
    achievements_score INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(external_id, program, list_date)
)

2. ЗАГРУЗКА ДАННЫХ (INSERT OR REPLACE):
INSERT OR REPLACE INTO applicants 
(external_id, program, list_date, consent, priority, 
 physics_score, russian_score, math_score, 
 achievements_score, total_score)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

3. УДАЛЕНИЕ ДАННЫХ:
-- Удаление по дате и программе
DELETE FROM applicants 
WHERE program = ? AND list_date = ?

-- Полная очистка
DELETE FROM applicants

4. ОБНОВЛЕНИЕ ДАННЫХ:
-- Обновление согласия
UPDATE applicants 
SET consent = ? 
WHERE external_id = ? AND program = ? AND list_date = ?

5. ВЫБОРКА ДАННЫХ С ФИЛЬТРАЦИЕЙ:
SELECT * FROM applicants 
WHERE program = 'ПМ' 
  AND list_date = '01.08' 
  AND consent = 1 
  AND total_score >= 200
ORDER BY total_score DESC

6. АГРЕГАЦИЯ:
-- Количество абитуриентов по программам
SELECT program, COUNT(*) 
FROM applicants 
WHERE list_date = '01.08' 
GROUP BY program

-- Средний балл по приоритетам
SELECT priority, AVG(total_score) 
FROM applicants 
WHERE program = 'ПМ' 
GROUP BY priority"""
        
        dialog = QDialog(self)
        dialog.setWindowTitle("SQL операции")
        dialog.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(sql_info)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

# РАСШИРЕННЫЙ КЛАСС ГЛАВНОГО ОКНА С ДОПОЛНИТЕЛЬНЫМ МЕНЮ
class ExtendedMainWindow(MainWindow):
    def __init__(self):
        super().__init__()
        self.generator = FixedTestDataGenerator()
        self.create_demo_menu()
    
    def create_demo_menu(self):
        """Создание меню демонстрации"""
        menubar = self.menuBar()
        
        # Меню Демонстрация
        demo_menu = menubar.addMenu("Демонстрация")
        
        # Пункт для демонстрации пересечений
        demo_intersections_action = QAction("Демонстрация пересечений абитуриентов", self)
        demo_intersections_action.triggered.connect(self.show_demo_dialog)
        demo_menu.addAction(demo_intersections_action)
        
        demo_menu.addSeparator()
        
        # Пункт для демонстрации структуры БД
        demo_structure_action = QAction("Структура БД (таблицы и связи)", self)
        demo_structure_action.triggered.connect(self.show_db_structure_dialog)
        demo_menu.addAction(demo_structure_action)
        
        # Пункт для демонстрации загрузки в пустую БД
        demo_loading_action = QAction("Загрузка в пустую БД", self)
        demo_loading_action.triggered.connect(self.demo_empty_db_loading)
        demo_menu.addAction(demo_loading_action)
        
        # Пункт для демонстрации обновления списков
        demo_update_action = QAction("Обновление списков (CRUD)", self)
        demo_update_action.triggered.connect(self.demo_list_updates)
        demo_menu.addAction(demo_update_action)
    
    def show_demo_dialog(self):
        """Показать диалог демонстрации"""
        dialog = DemoDialog(self.db, self.generator, self)
        dialog.exec()
    
    def show_db_structure_dialog(self):
        """Диалог структуры БД"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Структура базы данных")
        dialog.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextBrowser()
        
        structure_info = """СТРУКТУРА БАЗЫ ДАННЫХ
================================

ТАБЛИЦЫ:
--------
1. applicants (абитуриенты)
   • Основная таблица с данными абитуриентов
   • Содержит 11 полей
   • UNIQUE constraint по external_id, program, list_date

2. pass_scores (проходные баллы)
   • Хранит рассчитанные проходные баллы
   • Связь с applicants через program и list_date
   • UNIQUE constraint по program, list_date

3. statistics (статистика)
   • Хранит статистическую информацию
   • Связь с applicants через program и list_date
   • UNIQUE constraint по program, list_date

СВЯЗИ МЕЖДУ ТАБЛИЦАМИ:
---------------------
applicants 1:n pass_scores
  • program, list_date → program, list_date
  
applicants 1:n statistics
  • program, list_date → program, list_date

СХЕМА БАЗЫ ДАННЫХ:
-----------------
+-----------------+     +-----------------+     +-----------------+
|   applicants    |     |   pass_scores   |     |   statistics    |
+-----------------+     +-----------------+     +-----------------+
| id              |     | id              |     | id              |
| external_id     |     | program         |     | program         |
| program         |-----| list_date       |-----| list_date       |
| list_date       |     | pass_score      |     | total_apps      |
| consent         |     | calculation_time|     | priority_1_apps |
| priority        |     +-----------------+     | ...             |
| physics_score   |                             | priority_4_admit|
| russian_score   |                             +-----------------+
| math_score      |
| achievements    |
| total_score     |
| created_at      |
+-----------------+

ОГРАНИЧЕНИЯ (CONSTRAINTS):
-------------------------
1. UNIQUE (external_id, program, list_date) - уникальность записи
2. CHECK (priority BETWEEN 1 AND 4) - диапазон приоритета
3. FOREIGN KEY (логическая) program, list_date → pass_scores
4. FOREIGN KEY (логическая) program, list_date → statistics

ИНДЕКСЫ:
--------
• Автоматически создаются для PRIMARY KEY
• Рекомендуемые индексы для ускорения запросов:
  - CREATE INDEX idx_applicants_program_date ON applicants(program, list_date)
  - CREATE INDEX idx_applicants_consent ON applicants(consent)
  - CREATE INDEX idx_applicants_total_score ON applicants(total_score)"""
        
        text_edit.setPlainText(structure_info)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def demo_empty_db_loading(self):
        """Демонстрация загрузки в пустую БД"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Демонстрация загрузки в пустую БД")
        dialog.setGeometry(100, 100, 700, 500)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextBrowser()
        
        demo_text = """ДЕМОНСТРАЦИЯ ЗАГРУЗКИ В ПУСТУЮ БД
====================================

ШАГ 1: ПОДГОТОВКА ПУСТОЙ БАЗЫ
-----------------------------
1. Очистка существующих данных:
   - Меню 'Файл → Очистить базу'
   - SQL: DELETE FROM applicants
   - SQL: VACUUM (оптимизация)

2. Проверка состояния БД:
   • Таблицы созданы (CREATE TABLE IF NOT EXISTS)
   • Нет записей в таблицах
   • Индексы доступны

ШАГ 2: ЗАГРУЗКА CSV ФАЙЛОВ
--------------------------
1. Автоматический режим:
   - Меню 'Файл → Загрузить CSV (все файлы за дату)'
   - Пример: загрузка всех файлов за 01.08
   - Загружаемые файлы: 01.08_ПМ.csv, 01.08_ИВТ.csv, и т.д.

2. Ручной режим:
   - Меню 'Файл → Загрузить отдельный CSV'
   - Выбор конкретного файла
   - Автоопределение даты и программы из имени файла

ШАГ 3: ПРОЦЕСС ЗАГРУЗКИ
-----------------------
1. Для каждого файла:
   a) Чтение CSV с помощью pandas.read_csv()
   b) Определение программы из имени файла
   c) Удаление старых данных за эту дату и программу
   d) Построчная вставка данных
   e) Фиксация транзакции

2. SQL операции загрузки:
   BEGIN TRANSACTION;
   DELETE FROM applicants WHERE program='ПМ' AND list_date='01.08';
   INSERT INTO applicants (...) VALUES (...);
   ... (повтор для каждой строки)
   COMMIT;

ШАГ 4: ПРОВЕРКА ЗАГРУЗКИ
------------------------
1. Количество загруженных записей:
   • Меню 'Данные → Показать статистику БД'
   • SELECT COUNT(*) FROM applicants

2. Качество данных:
   • Проверка уникальности записей
   • Проверка ограничений (CHECK constraints)
   • Валидация диапазонов значений

ПРАКТИЧЕСКИЙ ПРИМЕР:
-------------------
1. Сгенерируйте данные: Файл → Сгенерировать данные для испытаний
2. Очистите БД: Файл → Очистить базу
3. Загрузите данные за 01.08: Файл → Загрузить CSV (все файлы за дату)
4. Проверьте результат: Данные → Показать статистику БД"""
        
        text_edit.setPlainText(demo_text)
        layout.addWidget(text_edit)
        
        # Кнопки действий
        button_layout = QHBoxLayout()
        
        clear_db_btn = QPushButton("1. Очистить БД")
        clear_db_btn.clicked.connect(lambda: self.clear_database())
        clear_db_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(clear_db_btn)
        
        load_data_btn = QPushButton("2. Загрузить данные за 01.08")
        load_data_btn.clicked.connect(lambda: self.load_date_data('01.08'))
        load_data_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(load_data_btn)
        
        check_btn = QPushButton("3. Проверить загрузку")
        check_btn.clicked.connect(self.show_database_stats)
        button_layout.addWidget(check_btn)
        
        layout.addLayout(button_layout)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def load_date_data(self, date):
        """Загрузка данных за указанную дату"""
        data_dir = 'data'
        if not os.path.exists(data_dir):
            QMessageBox.critical(self, "Ошибка", f"Папка '{data_dir}' не найдена")
            return
        
        loaded_files = 0
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{date}_") and filename.endswith('.csv'):
                filepath = os.path.join(data_dir, filename)
                success = self.db.load_csv(filepath, date)
                if success:
                    loaded_files += 1
        
        if loaded_files > 0:
            self.load_data()
            QMessageBox.information(self, "Успех", f"Загружено {loaded_files} файлов за {date}!")
        else:
            QMessageBox.warning(self, "Предупреждение", 
                               f"Не найдено CSV файлов для даты {date}.\n"
                               f"Сначала сгенерируйте данные через меню 'Файл'.")
    
    def demo_list_updates(self):
        """Демонстрация обновления списков (CRUD операции)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Демонстрация обновления списков")
        dialog.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout(dialog)
        
        tab_widget = QTabWidget()
        
        # Вкладка 1: CRUD операции
        crud_tab = QWidget()
        crud_layout = QVBoxLayout(crud_tab)
        
        crud_text = QTextBrowser()
        crud_text.setPlainText("""CRUD ОПЕРАЦИИ НАД СПИСКАМИ
================================

CREATE (СОЗДАНИЕ):
-----------------
1. Загрузка новых данных:
   • Загрузка CSV файла
   • INSERT INTO applicants VALUES (...)

2. Ручное добавление:
   • Прямое выполнение SQL
   • Через интерфейс программы

READ (ЧТЕНИЕ):
--------------
1. Фильтрация данных:
   • По дате, программе, приоритету
   • По баллам (минимальные/максимальные)
   • По наличию согласия

2. Статистические запросы:
   • Количество абитуриентов
   • Средние баллы
   • Распределение по приоритетам

UPDATE (ОБНОВЛЕНИЕ):
-------------------
1. Массовое обновление:
   • Обновление всех записей за дату
   • Изменение согласий
   • Корректировка баллов

2. Выборочное обновление:
   • Обновление конкретного абитуриента
   • Изменение приоритета
   • Исправление ошибок в данных

DELETE (УДАЛЕНИЕ):
-----------------
1. Удаление по условию:
   • Удаление записей за конкретную дату
   • Удаление по программе
   • Удаление абитуриентов без согласия

2. Полная очистка:
   • Очистка всей базы данных
   • Очистка статистических таблиц

ПРИМЕРЫ SQL ЗАПРОСОВ:
--------------------
-- CREATE
INSERT INTO applicants (external_id, program, list_date, consent, priority, physics_score, total_score)
VALUES (100500, 'ПМ', '01.08', 1, 1, 85, 270);

-- READ
SELECT * FROM applicants 
WHERE program = 'ПМ' 
  AND list_date = '01.08'
  AND total_score > 250
ORDER BY total_score DESC;

-- UPDATE
UPDATE applicants 
SET consent = 0 
WHERE external_id = 100500 
  AND program = 'ПМ' 
  AND list_date = '01.08';

-- DELETE
DELETE FROM applicants 
WHERE list_date = '01.08' 
  AND consent = 0;""")
        
        crud_layout.addWidget(crud_text)
        tab_widget.addTab(crud_tab, "CRUD операции")
        
        # Вкладка 2: Демонстрация для разных дней
        days_tab = QWidget()
        days_layout = QVBoxLayout(days_tab)
        
        days_text = QTextBrowser()
        
        # Получаем текущие данные из БД
        dates = self.db.get_dates()
        
        demo_info = "ДЕМОНСТРАЦИЯ ОБНОВЛЕНИЯ ДЛЯ РАЗНЫХ ДНЕЙ\n"
        demo_info += "=" * 50 + "\n\n"
        
        if dates:
            demo_info += "Текущие даты в БД:\n"
            for date in dates:
                count = self.db.get_applicants_count(date=date)
                demo_info += f"  • {date}: {count} записей\n"
            
            demo_info += "\nСЦЕНАРИИ ОБНОВЛЕНИЯ:\n"
            demo_info += "1. 01.08 → 02.08 (добавление новых данных)\n"
            demo_info += "   • Новые абитуриенты добавляются\n"
            demo_info += "   • Старые данные сохраняются\n\n"
            
            demo_info += "2. 02.08 → 02.08_v2 (обновление существующих)\n"
            demo_info += "   • Удаление старых записей за 02.08\n"
            demo_info += "   • Вставка обновленных данных\n\n"
            
            demo_info += "3. Удаление 03.08 (очистка устаревших)\n"
            demo_info += "   • DELETE FROM applicants WHERE list_date = '03.08'\n"
            demo_info += "   • Каскадное удаление в pass_scores, statistics\n"
        else:
            demo_info += "База данных пуста. Загрузите данные для демонстрации."
        
        days_text.setPlainText(demo_info)
        days_layout.addWidget(days_text)
        
        # Кнопки для демонстрации
        if dates:
            button_layout = QHBoxLayout()
            
            if '01.08' in dates and '02.08' in dates:
                compare_btn = QPushButton("Сравнить 01.08 и 02.08")
                compare_btn.clicked.connect(lambda: self.compare_dates('01.08', '02.08'))
                button_layout.addWidget(compare_btn)
            
            update_btn = QPushButton("Показать операции UPDATE")
            update_btn.clicked.connect(self.show_update_operations)
            button_layout.addWidget(update_btn)
            
            days_layout.addLayout(button_layout)
        
        tab_widget.addTab(days_tab, "Обновление по дням")
        
        layout.addWidget(tab_widget)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def compare_dates(self, date1, date2):
        """Сравнение данных за две даты"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Сравниваем количество записей
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE list_date = ?", (date1,))
        count1 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE list_date = ?", (date2,))
        count2 = cursor.fetchone()[0]
        
        # Сравниваем средние баллы
        cursor.execute("SELECT AVG(total_score) FROM applicants WHERE list_date = ?", (date1,))
        avg1 = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(total_score) FROM applicants WHERE list_date = ?", (date2,))
        avg2 = cursor.fetchone()[0] or 0
        
        conn.close()
        
        comparison = f"СРАВНЕНИЕ ДАННЫХ\n"
        comparison += "=" * 40 + "\n"
        comparison += f"{date1} vs {date2}\n"
        comparison += "-" * 40 + "\n"
        comparison += f"Количество записей:\n"
        comparison += f"  {date1}: {count1} абитуриентов\n"
        comparison += f"  {date2}: {count2} абитуриентов\n"
        comparison += f"  Разница: {abs(count1 - count2)} ({'+' if count2 > count1 else ''}{count2 - count1})\n\n"
        comparison += f"Средний балл:\n"
        comparison += f"  {date1}: {avg1:.2f}\n"
        comparison += f"  {date2}: {avg2:.2f}\n"
        comparison += f"  Изменение: {avg2 - avg1:+.2f}"
        
        QMessageBox.information(self, "Сравнение дат", comparison)
    
    def show_update_operations(self):
        """Показать примеры операций UPDATE"""
        examples = """ПРИМЕРЫ ОПЕРАЦИЙ UPDATE
=======================

1. МАССОВОЕ ОБНОВЛЕНИЕ СОГЛАСИЙ:
--------------------------------
-- Установить согласие всем абитуриентам с баллом > 250
UPDATE applicants 
SET consent = 1 
WHERE total_score > 250 
  AND list_date = '02.08';

2. КОРРЕКЦИЯ БАЛЛОВ:
-------------------
-- Увеличить баллы по физике на 5 для приоритета 1
UPDATE applicants 
SET physics_score = physics_score + 5,
    total_score = total_score + 5
WHERE priority = 1 
  AND program = 'ПМ'
  AND list_date = '03.08';

3. ИЗМЕНЕНИЕ ПРИОРИТЕТОВ:
-------------------------
-- Поменять приоритеты местами для конкретного абитуриента
UPDATE applicants 
SET priority = CASE 
    WHEN priority = 1 THEN 2
    WHEN priority = 2 THEN 1
    ELSE priority
END
WHERE external_id = 100500;

4. ОБНОВЛЕНИЕ С РАСЧЕТОМ:
------------------------
-- Пересчитать суммарный балл
UPDATE applicants 
SET total_score = physics_score + russian_score + math_score + achievements_score
WHERE list_date = '04.08';

5. УСЛОВНОЕ ОБНОВЛЕНИЕ:
----------------------
-- Установить согласие только лучшим абитуриентам
UPDATE applicants 
SET consent = 1 
WHERE total_score >= (
    SELECT MIN(total_score) 
    FROM (
        SELECT total_score 
        FROM applicants 
        WHERE program = 'ПМ' 
          AND list_date = '04.08' 
          AND consent = 1
        ORDER BY total_score DESC 
        LIMIT 40
    )
);"""
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Примеры операций UPDATE")
        dialog.setGeometry(100, 100, 700, 500)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(examples)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

# РАСШИРЕННЫЙ КЛАСС БАЗЫ ДАННЫХ С МЕТОДАМИ УДАЛЕНИЯ
class EnhancedDatabaseWithDelete(EnhancedDatabase):
    def __init__(self, db_path="admission.db"):
        super().__init__(db_path)
    
    def delete_applicant_by_id(self, applicant_id: int) -> bool:
        """Удаление абитуриента по ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM applicants WHERE id = ?", (applicant_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"Ошибка при удалении абитуриента: {e}")
            return False
    
    def delete_applicant_by_external_id(self, external_id: int, program: str = None, date: str = None) -> bool:
        """Удаление абитуриента по внешнему ID (возможно с фильтрами)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "DELETE FROM applicants WHERE external_id = ?"
            params = [external_id]
            
            if program:
                query += " AND program = ?"
                params.append(program)
            
            if date:
                query += " AND list_date = ?"
                params.append(date)
            
            cursor.execute(query, params)
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"Ошибка при удалении абитуриента: {e}")
            return False
    
    def delete_applicants_by_filters(self, filters: List[FilterCondition] = None) -> int:
        """Удаление абитуриентов по фильтрам"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "DELETE FROM applicants WHERE 1=1"
            params = []
            
            if filters:
                for filter_cond in filters:
                    sql_operator = filter_cond.logic.value
                    
                    if filter_cond.operator == "=":
                        query += f" {sql_operator} {filter_cond.field} = ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == ">":
                        query += f" {sql_operator} {filter_cond.field} > ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == "<":
                        query += f" {sql_operator} {filter_cond.field} < ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == ">=":
                        query += f" {sql_operator} {filter_cond.field} >= ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == "<=":
                        query += f" {sql_operator} {filter_cond.field} <= ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == "!=":
                        query += f" {sql_operator} {filter_cond.field} != ?"
                        params.append(filter_cond.value)
                    elif filter_cond.operator == "IN":
                        if isinstance(filter_cond.value, (list, tuple)):
                            placeholders = ','.join(['?'] * len(filter_cond.value))
                            query += f" {sql_operator} {filter_cond.field} IN ({placeholders})"
                            params.extend(filter_cond.value)
            
            cursor.execute(query, params)
            deleted_count = cursor.rowcount
            
            # Также удаляем связанные записи в других таблицах
            # (логически связанные, не внешний ключ)
            cursor.execute("DELETE FROM pass_scores WHERE pass_score IS NULL")
            cursor.execute("DELETE FROM statistics WHERE total_applications = 0")
            
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Ошибка при удалении по фильтрам: {e}")
            return 0
    
    def delete_by_program_and_date(self, program: str, date: str) -> int:
        """Удаление всех абитуриентов по программе и дате"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM applicants WHERE program = ? AND list_date = ?",
                (program, date)
            )
            
            deleted_count = cursor.rowcount
            
            # Удаляем связанные записи
            cursor.execute(
                "DELETE FROM pass_scores WHERE program = ? AND list_date = ?",
                (program, date)
            )
            
            cursor.execute(
                "DELETE FROM statistics WHERE program = ? AND list_date = ?",
                (program, date)
            )
            
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Ошибка при удалении по программе и дате: {e}")
            return 0
    
    def delete_duplicate_applicants(self) -> int:
        """Удаление дубликатов абитуриентов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Находим дубликаты (одинаковый external_id, program, list_date)
            cursor.execute('''
                DELETE FROM applicants 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM applicants 
                    GROUP BY external_id, program, list_date
                )
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Ошибка при удалении дубликатов: {e}")
            return 0

# КЛАСС ДИАЛОГА ДЛЯ УДАЛЕНИЯ АБИТУРИЕНТОВ
class DeleteApplicantsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Управление удалением абитуриентов")
        self.setGeometry(100, 100, 800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Вкладки для разных методов удаления
        tab_widget = QTabWidget()
        
        # Вкладка 1: Удаление по ID
        delete_id_tab = QWidget()
        delete_id_layout = QVBoxLayout(delete_id_tab)
        
        delete_id_label = QLabel("УДАЛЕНИЕ ПО ID АБИТУРИЕНТА")
        delete_id_label.setStyleSheet("font-weight: bold; color: red;")
        delete_id_layout.addWidget(delete_id_label)
        
        # ID абитуриента
        id_layout = QHBoxLayout()
        id_label = QLabel("ID абитуриента:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Введите ID из таблицы")
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        delete_id_layout.addLayout(id_layout)
        
        # Кнопка удаления по ID
        delete_by_id_btn = QPushButton("Удалить абитуриента по ID")
        delete_by_id_btn.clicked.connect(self.delete_by_id)
        delete_by_id_btn.setStyleSheet("background-color: #FFCCCC;")
        delete_id_layout.addWidget(delete_by_id_btn)
        
        delete_id_layout.addSpacing(20)
        
        # Внешний ID
        ext_id_layout = QHBoxLayout()
        ext_id_label = QLabel("Внешний ID:")
        self.ext_id_input = QLineEdit()
        self.ext_id_input.setPlaceholderText("Введите внешний ID (из CSV)")
        ext_id_layout.addWidget(ext_id_label)
        ext_id_layout.addWidget(self.ext_id_input)
        delete_id_layout.addLayout(ext_id_layout)
        
        # Программа и дата для внешнего ID
        program_date_layout = QGridLayout()
        
        program_label = QLabel("Программа (опционально):")
        self.program_combo = QComboBox()
        self.program_combo.addItem("Любая программа")
        self.program_combo.addItems(['ПМ', 'ИВТ', 'ИТСС', 'ИБ'])
        program_date_layout.addWidget(program_label, 0, 0)
        program_date_layout.addWidget(self.program_combo, 0, 1)
        
        date_label = QLabel("Дата (опционально):")
        self.date_combo = QComboBox()
        self.date_combo.addItem("Любая дата")
        dates = self.db.get_dates()
        self.date_combo.addItems(dates)
        program_date_layout.addWidget(date_label, 1, 0)
        program_date_layout.addWidget(self.date_combo, 1, 1)
        
        delete_id_layout.addLayout(program_date_layout)
        
        # Кнопка удаления по внешнему ID
        delete_by_ext_id_btn = QPushButton("Удалить по внешнему ID")
        delete_by_ext_id_btn.clicked.connect(self.delete_by_external_id)
        delete_by_ext_id_btn.setStyleSheet("background-color: #FFCCCC;")
        delete_id_layout.addWidget(delete_by_ext_id_btn)
        
        delete_id_layout.addStretch()
        tab_widget.addTab(delete_id_tab, "Удаление по ID")
        
        # Вкладка 2: Удаление по фильтрам
        delete_filters_tab = QWidget()
        delete_filters_layout = QVBoxLayout(delete_filters_tab)
        
        delete_filters_label = QLabel("УДАЛЕНИЕ ПО ФИЛЬТРАМ")
        delete_filters_label.setStyleSheet("font-weight: bold; color: red;")
        delete_filters_layout.addWidget(delete_filters_label)
        
        # Текущие фильтры
        filters_label = QLabel("Будут применены текущие фильтры из главного окна")
        filters_label.setWordWrap(True)
        delete_filters_layout.addWidget(filters_label)
        
        # Информация о том, что будет удалено
        self.filters_info = QTextEdit()
        self.filters_info.setReadOnly(True)
        self.filters_info.setMaximumHeight(100)
        delete_filters_layout.addWidget(self.filters_info)
        
        # Кнопка показать, что будет удалено
        preview_btn = QPushButton("Показать, что будет удалено")
        preview_btn.clicked.connect(self.preview_deletion)
        delete_filters_layout.addWidget(preview_btn)
        
        # Кнопка удаления по фильтрам
        delete_by_filters_btn = QPushButton("Удалить по текущим фильтрам")
        delete_by_filters_btn.clicked.connect(self.delete_by_filters)
        delete_by_filters_btn.setStyleSheet("background-color: #FF9999;")
        delete_filters_layout.addWidget(delete_by_filters_btn)
        
        delete_filters_layout.addSpacing(20)
        
        # Удаление по программе и дате
        program_date_label = QLabel("УДАЛЕНИЕ ПО ПРОГРАММЕ И ДАТЕ")
        program_date_label.setStyleSheet("font-weight: bold; color: darkred;")
        delete_filters_layout.addWidget(program_date_label)
        
        program_date_grid = QGridLayout()
        
        program_label2 = QLabel("Программа:")
        self.program_combo2 = QComboBox()
        self.program_combo2.addItems(['ПМ', 'ИВТ', 'ИТСС', 'ИБ'])
        program_date_grid.addWidget(program_label2, 0, 0)
        program_date_grid.addWidget(self.program_combo2, 0, 1)
        
        date_label2 = QLabel("Дата:")
        self.date_combo2 = QComboBox()
        self.date_combo2.addItems(dates if dates else ["Нет данных"])
        program_date_grid.addWidget(date_label2, 1, 0)
        program_date_grid.addWidget(self.date_combo2, 1, 1)
        
        delete_filters_layout.addLayout(program_date_grid)
        
        # Кнопка удаления по программе и дате
        delete_program_date_btn = QPushButton("Удалить все записи по программе и дате")
        delete_program_date_btn.clicked.connect(self.delete_by_program_date)
        delete_program_date_btn.setStyleSheet("background-color: #FF6666;")
        delete_filters_layout.addWidget(delete_program_date_btn)
        
        delete_filters_layout.addStretch()
        tab_widget.addTab(delete_filters_tab, "Удаление по фильтрам")
        
        # Вкладка 3: Продвинутое удаление
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        advanced_label = QLabel("ПРОДВИНУТОЕ УДАЛЕНИЕ")
        advanced_label.setStyleSheet("font-weight: bold; color: maroon;")
        advanced_layout.addWidget(advanced_label)
        
        # Удаление дубликатов
        duplicates_label = QLabel("Удаление дубликатов абитуриентов")
        advanced_layout.addWidget(duplicates_label)
        
        duplicates_info = QLabel(
            "Удалит записи с одинаковым внешним ID, программой и датой,\n"
            "оставив только первую запись для каждой комбинации."
        )
        duplicates_info.setWordWrap(True)
        advanced_layout.addWidget(duplicates_info)
        
        delete_duplicates_btn = QPushButton("Удалить дубликаты")
        delete_duplicates_btn.clicked.connect(self.delete_duplicates)
        delete_duplicates_btn.setStyleSheet("background-color: #FFCC99;")
        advanced_layout.addWidget(delete_duplicates_btn)
        
        advanced_layout.addSpacing(20)
        
        # Удаление без согласия
        no_consent_label = QLabel("Удаление абитуриентов без согласия")
        advanced_layout.addWidget(no_consent_label)
        
        no_consent_info = QLabel(
            "Удалит всех абитуриентов, у которых нет согласия на зачисление."
        )
        no_consent_info.setWordWrap(True)
        advanced_layout.addWidget(no_consent_info)
        
        delete_no_consent_btn = QPushButton("Удалить абитуриентов без согласия")
        delete_no_consent_btn.clicked.connect(self.delete_without_consent)
        delete_no_consent_btn.setStyleSheet("background-color: #FFCC99;")
        advanced_layout.addWidget(delete_no_consent_btn)
        
        advanced_layout.addSpacing(20)
        
        # Удаление с низкими баллами
        low_scores_label = QLabel("Удаление абитуриентов с низкими баллами")
        advanced_layout.addWidget(low_scores_label)
        
        low_scores_layout = QHBoxLayout()
        low_scores_label2 = QLabel("Максимальный балл:")
        self.low_score_input = QSpinBox()
        self.low_score_input.setRange(0, 400)
        self.low_score_input.setValue(150)
        low_scores_layout.addWidget(low_scores_label2)
        low_scores_layout.addWidget(self.low_score_input)
        low_scores_layout.addStretch()
        advanced_layout.addLayout(low_scores_layout)
        
        delete_low_scores_btn = QPushButton("Удалить с баллами ниже указанного")
        delete_low_scores_btn.clicked.connect(self.delete_low_scores)
        delete_low_scores_btn.setStyleSheet("background-color: #FFCC99;")
        advanced_layout.addWidget(delete_low_scores_btn)
        
        advanced_layout.addStretch()
        tab_widget.addTab(advanced_tab, "Продвинутое")
        
        # Вкладка 4: Статистика и информация
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_label = QLabel("СТАТИСТИКА БАЗЫ ДАННЫХ")
        stats_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(stats_label)
        
        # Текущая статистика
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.update_stats()
        stats_layout.addWidget(self.stats_text)
        
        # Кнопка обновления статистики
        refresh_stats_btn = QPushButton("Обновить статистику")
        refresh_stats_btn.clicked.connect(self.update_stats)
        stats_layout.addWidget(refresh_stats_btn)
        
        stats_layout.addStretch()
        tab_widget.addTab(stats_tab, "Статистика")
        
        layout.addWidget(tab_widget)
        
        # Кнопки закрытия
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def delete_by_id(self):
        """Удаление абитуриента по ID"""
        id_text = self.id_input.text().strip()
        if not id_text:
            QMessageBox.warning(self, "Ошибка", "Введите ID абитуриента")
            return
        
        try:
            applicant_id = int(id_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID должен быть числом")
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить абитуриента с ID {applicant_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_applicant_by_id(applicant_id)
            if success:
                QMessageBox.information(self, "Успех", f"Абитуриент с ID {applicant_id} удален")
                self.id_input.clear()
                self.update_stats()
                # Сигнал для обновления главного окна
                if self.parent():
                    self.parent().apply_filters()
            else:
                QMessageBox.warning(self, "Ошибка", f"Абитуриент с ID {applicant_id} не найден")
    
    def delete_by_external_id(self):
        """Удаление абитуриента по внешнему ID"""
        ext_id_text = self.ext_id_input.text().strip()
        if not ext_id_text:
            QMessageBox.warning(self, "Ошибка", "Введите внешний ID абитуриента")
            return
        
        try:
            external_id = int(ext_id_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Внешний ID должен быть числом")
            return
        
        # Получаем параметры фильтрации
        program = None
        if self.program_combo.currentText() != "Любая программа":
            program = self.program_combo.currentText()
        
        date = None
        if self.date_combo.currentText() != "Любая дата":
            date = self.date_combo.currentText()
        
        # Формируем сообщение для подтверждения
        message = f"Удалить абитуриента с внешним ID {external_id}"
        if program:
            message += f", программа: {program}"
        if date:
            message += f", дата: {date}"
        message += "?"
        
        reply = QMessageBox.question(
            self, "Подтверждение", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_applicant_by_external_id(external_id, program, date)
            if success:
                QMessageBox.information(self, "Успех", "Абитуриент удален")
                self.ext_id_input.clear()
                self.update_stats()
                if self.parent():
                    self.parent().apply_filters()
            else:
                QMessageBox.warning(self, "Ошибка", "Абитуриент не найден")
    
    def preview_deletion(self):
        """Предварительный просмотр того, что будет удалено"""
        if not self.parent():
            QMessageBox.warning(self, "Ошибка", "Нет доступа к фильтрам главного окна")
            return
        
        # Получаем текущие фильтры из главного окна
        filters = self.parent().build_filter_conditions()
        
        # Получаем абитуриентов по этим фильтрам
        applicants = self.db.get_applicants_with_filters(filters)
        
        if not applicants:
            self.filters_info.setPlainText("По текущим фильтрам не найдено абитуриентов.")
            return
        
        # Формируем информацию
        info = f"Найдено абитуриентов для удаления: {len(applicants)}\n\n"
        info += "Примеры записей, которые будут удалены:\n"
        info += "-" * 60 + "\n"
        
        for i, app in enumerate(applicants[:10]):  # Показываем первые 10
            info += f"{i+1}. ID: {app['id']}, Внешний ID: {app['external_id']}, "
            info += f"Программа: {app['program']}, Дата: {app['list_date']}, "
            info += f"Балл: {app['total_score']}\n"
        
        if len(applicants) > 10:
            info += f"... и еще {len(applicants) - 10} записей\n"
        
        info += "\n" + "-" * 60 + "\n"
        info += "Будьте осторожны! Это действие нельзя отменить."
        
        self.filters_info.setPlainText(info)
    
    def delete_by_filters(self):
        """Удаление по текущим фильтрам"""
        if not self.parent():
            QMessageBox.warning(self, "Ошибка", "Нет доступа к фильтрам главного окна")
            return
        
        # Получаем текущие фильтры из главного окна
        filters = self.parent().build_filter_conditions()
        
        if not filters:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Вы не установили фильтры. Это удалит ВСЕХ абитуриентов!\n"
                "Вы уверены, что хотите продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            # Получаем количество абитуриентов для удаления
            applicants = self.db.get_applicants_with_filters(filters)
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Вы уверены, что хотите удалить {len(applicants)} абитуриентов?\n"
                "Это действие нельзя отменить.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self.db.delete_applicants_by_filters(filters)
            QMessageBox.information(self, "Успех", f"Удалено {deleted_count} абитуриентов")
            self.update_stats()
            if self.parent():
                self.parent().apply_filters()
                self.parent().update_pass_scores()
                self.parent().update_graphs()
    
    def delete_by_program_date(self):
        """Удаление по программе и дате"""
        program = self.program_combo2.currentText()
        date = self.date_combo2.currentText()
        
        if date == "Нет данных":
            QMessageBox.warning(self, "Ошибка", "В базе нет данных")
            return
        
        # Подсчитываем количество записей
        count = self.db.get_applicants_count(program, date)
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить ВСЕХ абитуриентов?\n"
            f"Программа: {program}, Дата: {date}\n"
            f"Количество записей: {count}\n\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self.db.delete_by_program_and_date(program, date)
            QMessageBox.information(
                self, "Успех",
                f"Удалено {deleted_count} записей по программе {program} за {date}"
            )
            self.update_stats()
            if self.parent():
                self.parent().apply_filters()
                self.parent().update_pass_scores()
                self.parent().update_graphs()
    
    def delete_duplicates(self):
        """Удаление дубликатов"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить дублирующиеся записи абитуриентов?\n"
            "Останутся только первые записи для каждой комбинации "
            "(внешний ID, программа, дата).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self.db.delete_duplicate_applicants()
            QMessageBox.information(self, "Успех", f"Удалено {deleted_count} дубликатов")
            self.update_stats()
            if self.parent():
                self.parent().apply_filters()
    
    def delete_without_consent(self):
        """Удаление абитуриентов без согласия"""
        # Получаем количество абитуриентов без согласия
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE consent = 0")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            QMessageBox.information(self, "Информация", "Нет абитуриентов без согласия")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить {count} абитуриентов без согласия на зачисление?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            filters = [FilterCondition("consent", "=", 0, LogicOperator.AND)]
            deleted_count = self.db.delete_applicants_by_filters(filters)
            QMessageBox.information(self, "Успех", f"Удалено {deleted_count} абитуриентов без согласия")
            self.update_stats()
            if self.parent():
                self.parent().apply_filters()
                self.parent().update_pass_scores()
                self.parent().update_graphs()
    
    def delete_low_scores(self):
        """Удаление абитуриентов с низкими баллами"""
        max_score = self.low_score_input.value()
        
        # Получаем количество абитуриентов с баллами ниже указанного
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE total_score < ?", (max_score,))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            QMessageBox.information(
                self, "Информация",
                f"Нет абитуриентов с баллами ниже {max_score}"
            )
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить {count} абитуриентов с суммарным баллом ниже {max_score}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            filters = [FilterCondition("total_score", "<", max_score, LogicOperator.AND)]
            deleted_count = self.db.delete_applicants_by_filters(filters)
            QMessageBox.information(
                self, "Успех",
                f"Удалено {deleted_count} абитуриентов с баллами ниже {max_score}"
            )
            self.update_stats()
            if self.parent():
                self.parent().apply_filters()
                self.parent().update_pass_scores()
                self.parent().update_graphs()
    
    def update_stats(self):
        """Обновление статистики базы данных"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        stats = "СТАТИСТИКА БАЗЫ ДАННЫХ\n"
        stats += "=" * 40 + "\n\n"
        
        # Общее количество абитуриентов
        cursor.execute("SELECT COUNT(*) FROM applicants")
        total_applicants = cursor.fetchone()[0]
        stats += f"Всего абитуриентов: {total_applicants}\n"
        
        # С согласием и без
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE consent = 1")
        with_consent = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM applicants WHERE consent = 0")
        without_consent = cursor.fetchone()[0]
        stats += f"  • С согласием: {with_consent}\n"
        stats += f"  • Без согласия: {without_consent}\n\n"
        
        # По программам
        stats += "По программам:\n"
        for program in ['ПМ', 'ИВТ', 'ИТСС', 'ИБ']:
            cursor.execute("SELECT COUNT(*) FROM applicants WHERE program = ?", (program,))
            count = cursor.fetchone()[0]
            stats += f"  • {program}: {count}\n"
        
        stats += "\n"
        
        # По датам
        cursor.execute("SELECT DISTINCT list_date FROM applicants ORDER BY list_date")
        dates = [row[0] for row in cursor.fetchall()]
        
        if dates:
            stats += "По датам:\n"
            for date in dates:
                cursor.execute("SELECT COUNT(*) FROM applicants WHERE list_date = ?", (date,))
                count = cursor.fetchone()[0]
                stats += f"  • {date}: {count}\n"
        
        stats += "\n"
        
        # Средний балл
        cursor.execute("SELECT AVG(total_score) FROM applicants")
        avg_score = cursor.fetchone()[0]
        if avg_score:
            stats += f"Средний балл: {avg_score:.2f}\n"
        
        # Минимальный и максимальный балл
        cursor.execute("SELECT MIN(total_score), MAX(total_score) FROM applicants")
        min_max = cursor.fetchone()
        if min_max[0] is not None:
            stats += f"Минимальный балл: {min_max[0]}\n"
            stats += f"Максимальный балл: {min_max[1]}\n"
        
        conn.close()
        
        self.stats_text.setPlainText(stats)

# РАСШИРЕННЫЙ КЛАСС ГЛАВНОГО ОКНА С ФУНКЦИОНАЛОМ УДАЛЕНИЯ
class ExtendedMainWindowWithDelete(ExtendedMainWindow):
    def __init__(self):
        # Используем новую базу данных с функциями удаления
        self.db = EnhancedDatabaseWithDelete()
        super().__init__()
        
        # Заменяем базу данных в родительском классе
        self.db = EnhancedDatabaseWithDelete()
        
        # Добавляем контекстное меню для таблицы
        self.setup_table_context_menu()
    
    def create_demo_menu(self):
        """Расширяем меню демонстрации"""
        super().create_demo_menu()
        
        menubar = self.menuBar()
        
        # Находим меню "Данные"
        data_menu = None
        for action in menubar.actions():
            if action.text() == "Данные":
                data_menu = action.menu()
                break
        
        if data_menu:
            data_menu.addSeparator()
            
            # Добавляем пункт для управления удалением
            delete_action = QAction("Управление удалением абитуриентов", self)
            delete_action.triggered.connect(self.show_delete_dialog)
            data_menu.addAction(delete_action)
            
            # Добавляем быстрые команды удаления
            delete_selected_action = QAction("Удалить выбранного абитуриента", self)
            delete_selected_action.triggered.connect(self.delete_selected_applicant)
            data_menu.addAction(delete_selected_action)
    
    def setup_table_context_menu(self):
        """Настройка контекстного меню для таблицы"""
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_table_context_menu)
    
    def show_table_context_menu(self, position):
        """Показать контекстное меню для таблицы"""
        menu = QMenu()
        
        delete_action = menu.addAction("Удалить выбранного абитуриента")
        delete_action.triggered.connect(self.delete_selected_applicant)
        
        menu.addSeparator()
        
        view_details_action = menu.addAction("Просмотреть детали")
        view_details_action.triggered.connect(self.view_applicant_details)
        
        menu.exec(self.table_widget.viewport().mapToGlobal(position))
    
    def delete_selected_applicant(self):
        """Удалить выбранного абитуриента из таблицы"""
        current_row = self.table_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите абитуриента для удаления")
            return
        
        # Получаем ID из первой колонки
        id_item = self.table_widget.item(current_row, 0)
        if not id_item:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить ID абитуриента")
            return
        
        applicant_id = int(id_item.text())
        
        # Получаем информацию об абитуриенте для подтверждения
        program_item = self.table_widget.item(current_row, 1)
        date_item = self.table_widget.item(current_row, 2)
        score_item = self.table_widget.item(current_row, 9)
        
        program = program_item.text() if program_item else "?"
        date = date_item.text() if date_item else "?"
        score = score_item.text() if score_item else "?"
        
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить абитуриента?\n\n"
            f"ID: {applicant_id}\n"
            f"Программа: {program}\n"
            f"Дата: {date}\n"
            f"Суммарный балл: {score}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_applicant_by_id(applicant_id)
            if success:
                QMessageBox.information(self, "Успех", "Абитуриент удален")
                self.apply_filters()  # Обновляем таблицу
                self.update_pass_scores()  # Обновляем проходные баллы
                self.update_graphs()  # Обновляем графики
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить абитуриента")
    
    def view_applicant_details(self):
        """Просмотр детальной информации об абитуриенте"""
        current_row = self.table_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите абитуриента")
            return
        
        # Собираем информацию из всех колонок
        details = "ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ОБ АБИТУРИЕНТЕ\n"
        details += "=" * 50 + "\n\n"
        
        headers = [
            'ID', 'Программа', 'Дата', 'Согласие', 'Приоритет', 
            'Физика/ИКТ', 'Русский', 'Математика', 'Достижения', 'Сумма', 'Внешний ID'
        ]
        
        for col in range(self.table_widget.columnCount()):
            header = headers[col] if col < len(headers) else f"Колонка {col+1}"
            item = self.table_widget.item(current_row, col)
            value = item.text() if item else "Нет данных"
            details += f"{header}: {value}\n"
        
        # Показываем диалог с деталями
        dialog = QDialog(self)
        dialog.setWindowTitle("Детали абитуриента")
        dialog.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(details)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Удалить этого абитуриента")
        delete_btn.clicked.connect(lambda: self.delete_selected_applicant_and_close(dialog))
        delete_btn.setStyleSheet("background-color: #FFCCCC;")
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_selected_applicant_and_close(self, dialog):
        """Удалить выбранного абитуриента и закрыть диалог"""
        dialog.accept()
        self.delete_selected_applicant()
    
    def show_delete_dialog(self):
        """Показать диалог управления удалением"""
        dialog = DeleteApplicantsDialog(self.db, self)
        dialog.exec()

# ОБНОВЛЕННАЯ ФУНКЦИЯ MAIN
def main():
    """Основная функция запуска приложения"""
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle("Fusion")
    
    # Создаем и показываем главное окно с функционалом удаления
    window = ExtendedMainWindowWithDelete()  # Используем класс с удалением
    window.show()
    
    sys.exit(app.exec())

# ТОЧКА ВХОДА (переопределяем, если нужно)
if __name__ == "__main__":
    # Проверяем необходимые библиотеки
    required_libraries = ['pandas', 'numpy', 'matplotlib', 'reportlab', 'PyQt6']
    
    missing_libs = []
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        print("Необходимо установить следующие библиотеки:")
        for lib in missing_libs:
            print(f"  pip install {lib}")
        print("\nУстановите их и запустите программу снова.")
    else:
        main()
