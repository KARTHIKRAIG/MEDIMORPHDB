import re
import json
from datetime import datetime, timedelta
import numpy as np

class AIProcessor:
    def __init__(self):
        # Initialize with rule-based extraction only
        print("Using rule-based extraction for medication information")
        
        # Common medication names and their variations
        self.medication_database = {
            'aspirin': ['aspirin', 'acetylsalicylic acid', 'asa'],
            'ibuprofen': ['ibuprofen', 'advil', 'motrin', 'brufen'],
            'acetaminophen': ['acetaminophen', 'paracetamol', 'tylenol'],
            'amoxicillin': ['amoxicillin', 'amoxil', 'trimox'],
            'augmentin': ['augmentin'],
            'metformin': ['metformin', 'glucophage'],
            'lisinopril': ['lisinopril', 'prinivil', 'zestril'],
            'atorvastatin': ['atorvastatin', 'lipitor'],
            'omeprazole': ['omeprazole', 'prilosec'],
            'pand': ['pand'],
            'simvastatin': ['simvastatin', 'zocor'],
            'metoprolol': ['metoprolol', 'lopressor', 'toprol'],
            'losartan': ['losartan', 'cozaar'],
            'amlodipine': ['amlodipine', 'norvasc'],
            'hydrochlorothiazide': ['hydrochlorothiazide', 'hctz', 'microzide'],
            'pantoprazole': ['pantoprazole', 'protonix'],
            'carvedilol': ['carvedilol', 'coreg'],
            'furosemide': ['furosemide', 'lasix'],
            'spironolactone': ['spironolactone', 'aldactone'],
            'tramadol': ['tramadol', 'ultram'],
            'gabapentin': ['gabapentin', 'neurontin'],
            'duloxetine': ['duloxetine', 'cymbalta'],
            'enzoflam': ['enzoflam'],
            'hexigel': ['hexigel'],
            # Pediatric medications from prescription samples
            'calpol': ['calpol', 'syp calpol'],
            'delcon': ['delcon', 'syp delcon'],
            'levolin': ['levolin', 'syp levolin'],
            'meftol': ['meftol', 'meftol-p', 'syp meftol', 'syp meftol-p'],
            # Adult medications from prescription samples
            'abciximab': ['abciximab', 'tab abciximab'],
            'vomilast': ['vomilast', 'tab vomilast'],
            'zoclar': ['zoclar', 'cap zoclar'],
            'gestakind': ['gestakind', 'tab gestakind']
        }
        
        # Enhanced frequency patterns with Indian prescription timing format
        self.frequency_patterns = {
            'once daily (morning)': ['once daily', 'once a day', 'qd', 'q.d.', 'daily', 'every 24 hours', '1-0-0', '1 0 0'],
            'twice daily (morning & night)': ['twice daily', 'twice a day', 'bid', 'b.i.d.', 'every 12 hours', '1-0-1', '1 0 1'],
            'three times daily (morning, afternoon & night)': ['three times daily', 'three times a day', 'tid', 't.i.d.', 'every 8 hours', '1-1-1', '1 1 1'],
            'twice daily (morning & afternoon)': ['1-1-0', '1 1 0'],
            'twice daily (afternoon & night)': ['0-1-1', '0 1 1'],
            'four times daily': ['four times daily', 'four times a day', 'qid', 'q.i.d.', 'every 6 hours'],
            'every 6 hours': ['every 6 hours', 'q6h', 'q.6.h.'],
            'every 8 hours': ['every 8 hours', 'q8h', 'q.8.h.'],
            'every 12 hours': ['every 12 hours', 'q12h', 'q.12.h.'],
            'as needed': ['as needed', 'prn', 'p.r.n.', 'when required', 'sos'],
            'before meals': ['before meals', 'ac', 'a.c.', 'ante cibum'],
            'after meals': ['after meals', 'pc', 'p.c.', 'post cibum', 'after food'],
            'at bedtime': ['at bedtime', 'hs', 'h.s.', 'hora somni', 'before sleep'],
            # Medical abbreviations from prescription samples
            'every 6 hours': ['q6h', 'qid', 'every 6 hours'],
            'three times daily': ['tds', 't.d.s.', 'three times daily'],
            'once daily (morning)': ['1 morning', 'morning'],
            'once daily (night)': ['1 night', 'night'],
            'twice daily (morning & night)': ['1 morning, 1 night', 'morning and night']
        }
        
        # Duration patterns
        self.duration_patterns = {
            'days': r'(\d+)\s*(days?|d)',
            'weeks': r'(\d+)\s*(weeks?|wks?|w)',
            'months': r'(\d+)\s*(months?|mos?|m)',
            'years': r'(\d+)\s*(years?|yrs?|y)'
        }
    
    def extract_medications(self, ocr_text):
        """Extract medication information from OCR text using rule-based methods"""
        medications = []
        
        # Clean and normalize text
        cleaned_text = self.clean_text(ocr_text)
        
        # Extract medications using rule-based methods
        extracted_meds = []
        
        # Method 1: Rule-based extraction
        rule_based_meds = self.rule_based_extraction(cleaned_text)
        extracted_meds.extend(rule_based_meds)
        
        # Method 2: Pattern-based extraction
        pattern_meds = self.pattern_based_extraction(cleaned_text)
        extracted_meds.extend(pattern_meds)
        
        # Remove duplicates and merge similar medications
        unique_medications = self.merge_medications(extracted_meds)
        
        return unique_medications
    
    def rule_based_extraction(self, text):
        """Extract medications using rule-based approach"""
        medications = []
        text_lower = text.lower()
        found_medications = set()  # Track found medications to avoid duplicates

        # Look for known medication names
        for med_name, variations in self.medication_database.items():
            medication_found = False
            for variation in variations:
                if variation in text_lower and med_name not in found_medications:
                    # Find dosage information near the medication name
                    dosage_info = self.extract_dosage_near_medication(text, variation)
                    frequency_info = self.extract_frequency_near_medication(text, variation)
                    duration_info = self.extract_duration_near_medication(text, variation)

                    # Get detailed timing instructions
                    timing_instructions = self.parse_timing_instructions(frequency_info)

                    medications.append({
                        'name': med_name.title(),
                        'dosage': dosage_info,
                        'frequency': frequency_info,
                        'duration': duration_info,
                        'instructions': timing_instructions,
                        'confidence': 0.8,
                        'source': 'rule_based'
                    })
                    found_medications.add(med_name)
                    medication_found = True
                    break

            if medication_found:
                continue

        return medications
    
    def pattern_based_extraction(self, text):
        """Extract medications using regex patterns"""
        medications = []
        
        # Enhanced patterns for better dosage extraction
        patterns = [
            # Standard format: Medication Name + Dosage + Unit
            r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            
            # With dosage form: Medication + Dosage + Unit + Form
            r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\s*(tablet|capsule|pill|dose|tab|caps)\b',
            
            # With frequency: Medication + Dosage + Unit + Frequency
            r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\s*(once|twice|thrice|daily|bid|tid|qid)\b',
            
            # Prescription format: Tab./Caps./Syr. + Medication + Dosage
            r'(Tab\.|Caps\.|Syr\.|Inj\.|Tablet|Capsule|Syrup|Injection)\s*(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            
            # With frequency codes: Medication + Dosage + Unit + Frequency Code
            r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\s*(1-0-1|1-0-0|1-1-1|0-0-1|1-1-0)\b',
            
            # Dosage first format: Dosage + Unit + Medication
            r'(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\s*(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\b',
            
            # With strength indicators: Medication + Strength + Dosage
            r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(?:strength|dose|dosage)?\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            
            # Common medication names with typical dosages
            r'(aspirin|ibuprofen|acetaminophen|paracetamol|amoxicillin|metformin|lisinopril|atorvastatin|omeprazole)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            
            # Pattern for Tab. format like "Tab. Augmentin 625mg"
            r'Tab\.\s*(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            
            # Pattern for medications without dosage like "Tab. Enzoflam"
            r'Tab\.\s*(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\b'
        ]
        
        found_medications = set()  # Track found medications to avoid duplicates

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()

                # Handle different pattern formats
                if len(groups) >= 4:  # Tab. format: (Tab., med_name, dosage, unit)
                    med_name = groups[1]
                    dosage_num = groups[2]
                    unit = groups[3]
                    dosage = f"{dosage_num} {unit}"
                elif len(groups) >= 3:  # Standard format: (med_name, dosage, unit)
                    med_name = groups[0]
                    dosage_num = groups[1]
                    unit = groups[2]
                    dosage = f"{dosage_num} {unit}"
                elif len(groups) == 2:  # Dosage first format: (dosage, unit, med_name)
                    if groups[0].isdigit() or '.' in groups[0]:
                        dosage_num = groups[0]
                        unit = groups[1]
                        # Look for medication name after the dosage
                        remaining_text = text[match.end():match.end()+50]
                        med_match = re.search(r'(\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\b', remaining_text)
                        med_name = med_match.group(1) if med_match else "Unknown Medication"
                        dosage = f"{dosage_num} {unit}"
                    else:
                        med_name = groups[0]
                        dosage = "1 tablet"  # Default dosage
                else:
                    med_name = groups[0]
                    dosage = "1 tablet"  # Default dosage

                # Skip if medication name is just a number or too short
                if not med_name or len(med_name.strip()) < 3 or med_name.strip().isdigit():
                    continue

                # Skip if we've already found this medication
                med_name_clean = med_name.strip().lower()
                if med_name_clean in found_medications:
                    continue

                # Extract additional information
                frequency_info = self.extract_frequency_near_medication(text, med_name)
                duration_info = self.extract_duration_near_medication(text, med_name)

                # Get detailed timing instructions
                timing_instructions = self.parse_timing_instructions(frequency_info)

                medications.append({
                    'name': med_name.title(),
                    'dosage': dosage,
                    'frequency': frequency_info,
                    'duration': duration_info,
                    'instructions': timing_instructions,
                    'confidence': 0.7,
                    'source': 'pattern_based'
                })
                found_medications.add(med_name_clean)
        
        return medications
    
    def extract_dosage_near_medication(self, text, medication_name):
        """Extract dosage information near a medication name with enhanced pattern matching"""
        # Enhanced dosage patterns for Indian prescriptions
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\b',
            r'(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|units?)\s*(tablet|capsule|pill|dose)\b',
            # Common Indian prescription dosages
            r'\b(625|500|250|125|40|20|10|5)\s*(mg|ml)\b',
            r'\b(\d{2,4})\s*(?:mg|ml)\b',  # 2-4 digit dosages
            # Handle garbled text where mg might be corrupted
            r'\b(\d{2,4})\s*(?:mg|ml|m|g)\b',
        ]

        # Find the position of the medication name (try fuzzy matching for garbled text)
        med_pos = text.lower().find(medication_name.lower())

        if med_pos == -1:
            # Try fuzzy matching for garbled medication names
            words = text.split()
            for i, word in enumerate(words):
                if self.fuzzy_match(word.lower(), medication_name.lower()):
                    # Found similar word, look around it
                    context_start = max(0, i-3)
                    context_end = min(len(words), i+4)
                    search_text = ' '.join(words[context_start:context_end])
                    break
            else:
                return "Unknown dosage"
        else:
            # Look for dosage patterns within 100 characters of the medication name
            start_pos = max(0, med_pos - 50)
            end_pos = min(len(text), med_pos + 150)
            search_text = text[start_pos:end_pos]

        for pattern in dosage_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple) and len(matches[0]) >= 2:
                    dosage_num, unit = matches[0][:2]
                    return f"{dosage_num} {unit}"
                elif isinstance(matches[0], str):
                    return f"{matches[0]} mg"
                else:
                    return f"{matches[0][0]} mg"

        # Look for any numbers that might be dosages (common prescription dosages)
        numbers = re.findall(r'\b(\d{2,4})\b', search_text)
        for num in numbers:
            num_val = int(num)
            if num_val in [625, 500, 250, 125, 100, 75, 50, 40, 25, 20, 10, 5]:
                return f"{num} mg"

        return "Unknown dosage"
    
    def extract_frequency_near_medication(self, text, medication_name):
        """Extract frequency information near a medication name with enhanced timing detection"""
        text_lower = text.lower()
        med_pos = text_lower.find(medication_name.lower())

        if med_pos == -1:
            # Try fuzzy matching for garbled medication names
            words = text.split()
            for i, word in enumerate(words):
                if self.fuzzy_match(word.lower(), medication_name.lower()):
                    context_start = max(0, i-3)
                    context_end = min(len(words), i+4)
                    search_text = ' '.join(words[context_start:context_end]).lower()
                    break
            else:
                return "daily"
        else:
            # Look for frequency patterns within 200 characters of the medication name
            start_pos = max(0, med_pos - 100)
            end_pos = min(len(text), med_pos + 200)
            search_text = text_lower[start_pos:end_pos]

        # Enhanced pattern matching for Indian prescription timing format
        timing_patterns = [
            (r'1-0-1|1 0 1', 'twice daily (morning & night)'),
            (r'1-1-1|1 1 1', 'three times daily (morning, afternoon & night)'),
            (r'1-0-0|1 0 0', 'once daily (morning)'),
            (r'0-0-1|0 0 1', 'once daily (night)'),
            (r'1-1-0|1 1 0', 'twice daily (morning & afternoon)'),
            (r'0-1-1|0 1 1', 'twice daily (afternoon & night)'),
            (r'2-0-2|2 0 2', 'twice daily (2 morning & 2 night)'),
            (r'1-2-1|1 2 1', 'four times daily (1 morning, 2 afternoon, 1 night)'),
        ]

        # Check for timing patterns first (more specific)
        for pattern, description in timing_patterns:
            if re.search(pattern, search_text):
                return description

        # Check for standard frequency patterns
        for frequency, patterns in self.frequency_patterns.items():
            for pattern in patterns:
                if pattern in search_text:
                    return frequency

        # Look for any timing pattern in the format X-Y-Z
        timing_match = re.search(r'(\d)-(\d)-(\d)', search_text)
        if timing_match:
            morning, afternoon, night = timing_match.groups()
            total_doses = int(morning) + int(afternoon) + int(night)

            if total_doses == 1:
                if morning == '1':
                    return 'once daily (morning)'
                elif afternoon == '1':
                    return 'once daily (afternoon)'
                else:
                    return 'once daily (night)'
            elif total_doses == 2:
                if morning == '1' and night == '1':
                    return 'twice daily (morning & night)'
                elif morning == '1' and afternoon == '1':
                    return 'twice daily (morning & afternoon)'
                else:
                    return 'twice daily (afternoon & night)'
            elif total_doses == 3:
                return 'three times daily (morning, afternoon & night)'
            else:
                return f'{total_doses} times daily'

        return "daily"

    def parse_timing_instructions(self, frequency_text):
        """Convert frequency text to detailed timing instructions"""
        timing_instructions = {
            'once daily (morning)': 'Take 1 dose in the morning',
            'once daily (afternoon)': 'Take 1 dose in the afternoon',
            'once daily (night)': 'Take 1 dose at night',
            'twice daily (morning & night)': 'Take 1 dose in the morning and 1 dose at night',
            'twice daily (morning & afternoon)': 'Take 1 dose in the morning and 1 dose in the afternoon',
            'twice daily (afternoon & night)': 'Take 1 dose in the afternoon and 1 dose at night',
            'three times daily (morning, afternoon & night)': 'Take 1 dose in the morning, 1 dose in the afternoon, and 1 dose at night',
        }

        return timing_instructions.get(frequency_text, frequency_text)

    def extract_duration_near_medication(self, text, medication_name):
        """Extract duration information near a medication name"""
        text_lower = text.lower()
        med_pos = text_lower.find(medication_name.lower())
        
        if med_pos == -1:
            return "7 days"
        
        # Look for duration patterns within 200 characters of the medication name
        start_pos = max(0, med_pos - 100)
        end_pos = min(len(text), med_pos + 200)
        search_text = text_lower[start_pos:end_pos]
        
        for duration_type, pattern in self.duration_patterns.items():
            match = re.search(pattern, search_text)
            if match:
                number = match.group(1)
                return f"{number} {duration_type}"
        
        return "7 days"
    
    def is_likely_medication(self, word):
        """Check if a word is likely to be a medication name"""
        # Common medication suffixes
        med_suffixes = ['ol', 'ine', 'ate', 'ide', 'am', 'il', 'in', 'an', 'ar', 'er']
        
        # Check if word ends with common medication suffixes
        for suffix in med_suffixes:
            if word.lower().endswith(suffix):
                return True
        
        # Check if word is in our medication database
        for med_name, variations in self.medication_database.items():
            if word.lower() in variations:
                return True
        
        return False
    
    def merge_medications(self, medications):
        """Merge similar medications and remove duplicates"""
        # Group medications by similar names first
        groups = {}

        for med in medications:
            med_name = med['name'].strip()

            # Skip invalid medications
            if (not med_name or len(med_name) < 2 or
                med_name.isdigit() or
                med_name.lower() in ['mg', 'ml', 'tablet', 'cap', 'tab', 'unknown medication']):
                continue

            # Find which group this medication belongs to
            group_key = None
            med_name_lower = med_name.lower()

            for existing_key in groups.keys():
                if (existing_key == med_name_lower or
                    existing_key in med_name_lower or
                    med_name_lower in existing_key):
                    group_key = existing_key
                    break

            if group_key is None:
                group_key = med_name_lower
                groups[group_key] = []

            groups[group_key].append(med)

        # Now merge each group into a single best medication
        merged = []
        for group_meds in groups.values():
            if not group_meds:
                continue

            # Find the best medication from the group by comparing all fields
            best_med = None
            best_score = -1

            for med in group_meds:
                # Score each medication based on information quality
                score = 0

                # Score dosage
                if 'mg' in med['dosage'] or 'ml' in med['dosage']:
                    score += 3
                elif 'tablet' in med['dosage']:
                    score += 1
                elif 'Unknown' not in med['dosage']:
                    score += 2

                # Score frequency
                if '1-0-1' in med['frequency'] or 'twice' in med['frequency']:
                    score += 2
                elif 'daily' not in med['frequency']:
                    score += 1

                # Score duration
                if '5 days' in med['duration'] or '1 week' in med['duration']:
                    score += 2
                elif '7 days' not in med['duration'] and any(char.isdigit() for char in med['duration']):
                    score += 1

                # Score confidence
                score += med.get('confidence', 0)

                if score > best_score:
                    best_score = score
                    best_med = med.copy()

            # Now merge any additional good information from other medications in the group
            for med in group_meds:
                if med == best_med:
                    continue

                # Enhance best_med with any better information
                if self.is_better_dosage(med['dosage'], best_med['dosage']):
                    best_med['dosage'] = med['dosage']

                if self.is_better_frequency(med['frequency'], best_med['frequency']):
                    best_med['frequency'] = med['frequency']

                if self.is_better_duration(med['duration'], best_med['duration']):
                    best_med['duration'] = med['duration']

                if med.get('instructions') and not best_med.get('instructions'):
                    best_med['instructions'] = med['instructions']

            merged.append(best_med)

        return merged

    def is_better_dosage(self, new_dosage, existing_dosage):
        """Check if new dosage is better than existing"""
        if 'Unknown' in existing_dosage and 'Unknown' not in new_dosage:
            return True
        if 'mg' in new_dosage and 'tablet' in existing_dosage:
            return True
        if 'ml' in new_dosage and 'tablet' in existing_dosage:
            return True
        return False

    def is_better_frequency(self, new_freq, existing_freq):
        """Check if new frequency is better than existing"""
        if 'daily' in existing_freq and ('1-0-1' in new_freq or 'twice' in new_freq or 'three' in new_freq):
            return True
        if len(new_freq) > len(existing_freq) and 'daily' not in new_freq:
            return True
        return False

    def is_better_duration(self, new_duration, existing_duration):
        """Check if new duration is better than existing"""
        if '7 days' in existing_duration and '7 days' not in new_duration:
            return True
        if '5 days' in new_duration and '7 days' in existing_duration:
            return True
        return False

    def clean_text(self, text):
        """Clean and normalize text for better processing"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common OCR artifacts but keep important characters for medical text
        text = re.sub(r'[^\w\s.,:;()\[\]{}/\-+=%]', ' ', text)

        # DO NOT replace digits - they are crucial for dosage information
        # Only fix obvious OCR mistakes in non-numeric contexts

        return text