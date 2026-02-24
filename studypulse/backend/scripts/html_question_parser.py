#!/usr/bin/env python3
"""
HTML Question Parser for NEET PG Question Banks

This script extracts questions from HTML files containing embedded JSON question data
and transforms them into a format compatible with the StudyPulse bulk import API.

Supports:
- Multiple topic sections in a single HTML file
- Question images and explanation images
- Audio/video metadata preservation
- Automatic topic mapping

Usage:
    python html_question_parser.py --input "questions.html" --output "questions_import.json"
    python html_question_parser.py --input "questions.html" --output "questions_import.json" --topic-map '{"topic_name": 1}'
"""

import json
import re
import argparse
import logging
from html import unescape
from typing import Any
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuestionHTMLParser:
    """Parser for extracting questions from HTML files with embedded JSON data."""
    
    def __init__(self, html_content: str, source_name: str = "HTML_IMPORT"):
        self.html = html_content
        self.source_name = source_name
        self.sections: list[dict] = []
        self.all_questions: list[dict] = []
        
    def parse(self) -> list[dict]:
        """Parse the HTML file and extract all questions."""
        logger.info("Starting HTML parsing...")
        
        # Extract topic sections from navigation buttons
        self._extract_topic_sections()
        logger.info(f"Found {len(self.sections)} topic sections")
        
        # Extract questions from each section's iframe srcdoc
        self._extract_all_questions()
        logger.info(f"Extracted {len(self.all_questions)} total questions")
        
        return self.all_questions
    
    def _extract_topic_sections(self) -> None:
        """Extract topic section names from navigation buttons."""
        # Pattern: <button onclick="showTest('test1')">Topic_Name</button>
        pattern = r'<button onclick="showTest\(\'test(\d+)\'\)">([^<]+)</button>'
        matches = re.findall(pattern, self.html)
        
        for test_id, topic_name in matches:
            self.sections.append({
                'test_id': test_id,
                'topic_name': topic_name.replace('_', ' ').replace('__', ', '),
                'raw_name': topic_name
            })
    
    def _extract_all_questions(self) -> None:
        """Extract questions from all iframe srcdoc attributes."""
        # Find all iframe srcdoc contents
        pattern = r'<iframe srcdoc="([^"]*)"'
        matches = re.findall(pattern, self.html)
        
        for idx, srcdoc in enumerate(matches):
            # Unescape HTML entities
            unescaped = unescape(srcdoc)
            
            # Find the questions JSON array
            questions = self._extract_questions_json(unescaped)
            
            if questions:
                # Get the topic for this section
                section_idx = idx  # Sections are in order
                topic_name = ""
                if section_idx < len(self.sections):
                    topic_name = self.sections[section_idx]['topic_name']
                
                # Add topic metadata to each question
                for q in questions:
                    q['_source_topic'] = topic_name
                    q['_section_index'] = section_idx
                
                self.all_questions.extend(questions)
    
    def _extract_questions_json(self, html_content: str) -> list[dict]:
        """Extract the questions JSON array from HTML content."""
        try:
            # First, unescape HTML entities
            unescaped = unescape(html_content)
            
            # Pattern: questions = [{...}];
            # There may be multiple matches - we need the one with actual data
            # (not the empty initialization: questions = [])
            start_pattern = r'questions\s*=\s*\['
            
            # Find all matches
            for match in re.finditer(start_pattern, unescaped):
                # Find the matching closing bracket
                start_pos = match.end() - 1  # Position of [
                bracket_count = 0
                end_pos = start_pos
                
                for i, char in enumerate(unescaped[start_pos:], start=start_pos):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos <= start_pos:
                    continue
                
                # Extract the JSON array
                json_str = unescaped[start_pos:end_pos]
                
                # Skip empty arrays (initialization)
                if len(json_str) <= 2:
                    continue
                
                # Try to parse JSON
                try:
                    questions = json.loads(json_str)
                    if questions:  # Non-empty array
                        return questions
                except json.JSONDecodeError:
                    continue
            
            # No valid questions found
            return []
            
        except Exception as e:
            logger.warning(f"Error extracting questions: {e}")
            return []
    
    def transform_for_import(
        self, 
        questions: list[dict], 
        topic_id_map: dict[str, int],
        default_topic_id: int = 1
    ) -> list[dict]:
        """
        Transform HTML JSON questions to QuestionImport format.
        
        Args:
            questions: List of questions from HTML
            topic_id_map: Mapping of topic names to database IDs
            default_topic_id: Default topic ID if no mapping found
            
        Returns:
            List of questions in QuestionImport format
        """
        import_ready = []
        
        for idx, q in enumerate(questions, start=1):
            try:
                # Transform options array to dict
                options_dict = {}
                for opt in q.get('options', []):
                    label = opt.get('label', '')
                    text = opt.get('text', '')
                    if label and text:
                        options_dict[label] = text
                
                # Validate we have 4 options
                if len(options_dict) != 4:
                    logger.warning(f"Question {idx}: Expected 4 options, got {len(options_dict)}")
                    # Pad missing options if needed
                    for label in ['A', 'B', 'C', 'D']:
                        if label not in options_dict:
                            options_dict[label] = f"Option {label}"
                
                # Extract correct answer letter
                correct_answer = q.get('correct_answer', 'A')
                if correct_answer and len(correct_answer) > 0:
                    correct_letter = correct_answer[0].upper()
                    if correct_letter not in ['A', 'B', 'C', 'D']:
                        correct_letter = 'A'
                else:
                    # Find from options
                    for opt in q.get('options', []):
                        if opt.get('correct', False):
                            correct_letter = opt.get('label', 'A')
                            break
                    else:
                        correct_letter = 'A'
                
                # Get topic ID
                source_topic = q.get('_source_topic', '')
                topic_id = topic_id_map.get(source_topic, default_topic_id)
                
                # Clean explanation - remove bot signature
                explanation = q.get('explanation', '')
                if explanation:
                    # Remove the bot signature line
                    explanation = re.sub(
                        r"<p style='font-size: 10px; color: #808080; font-style: italic;'>@[^<]+</p>",
                        '',
                        explanation
                    ).strip()
                
                # Build import-ready question
                import_question = {
                    "topic_id": topic_id,
                    "question_text": q.get('text', '').strip(),
                    "options": options_dict,
                    "correct_answer": correct_letter,
                    "explanation": explanation if explanation else None,
                    "source": "WEB",
                    "difficulty": "medium",
                    # Image support (for enhanced schema)
                    "_question_images": q.get('question_images', []),
                    "_explanation_images": q.get('explanation_images', []),
                    "_audio_url": q.get('audio', ''),
                    "_video_url": q.get('video', ''),
                    "_source_topic": source_topic,
                    "_original_index": idx
                }
                
                import_ready.append(import_question)
                
            except Exception as e:
                logger.error(f"Failed to transform question {idx}: {e}")
                continue
        
        return import_ready


def generate_import_json(
    questions: list[dict],
    output_path: str,
    include_images: bool = True
) -> dict:
    """
    Generate the final JSON file for bulk import.
    
    Args:
        questions: Transformed questions
        output_path: Path to save the JSON file
        include_images: Whether to include image URLs
        
    Returns:
        The generated import data
    """
    # Separate into standard import and extended data
    standard_questions = []
    extended_data = []
    
    for q in questions:
        # Standard QuestionImport fields
        standard = {
            "topic_id": q["topic_id"],
            "question_text": q["question_text"],
            "options": q["options"],
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "source": q["source"],
            "difficulty": q["difficulty"]
        }
        standard_questions.append(standard)
        
        # Extended data (for image support)
        if include_images:
            extended = {
                "question_index": len(standard_questions) - 1,
                "question_images": q.get("_question_images", []),
                "explanation_images": q.get("_explanation_images", []),
                "audio_url": q.get("_audio_url", ""),
                "video_url": q.get("_video_url", ""),
                "source_topic": q.get("_source_topic", "")
            }
            extended_data.append(extended)
    
    import_data = {
        "questions": standard_questions,
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_questions": len(standard_questions),
            "source": "HTML_IMPORT",
            "has_image_support": include_images
        }
    }
    
    if include_images and extended_data:
        import_data["extended_data"] = extended_data
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(import_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(standard_questions)} questions to {output_path}")
    
    return import_data


def generate_topic_mapping_report(questions: list[dict]) -> dict:
    """Generate a report of topics found in the questions."""
    topics = {}
    
    for q in questions:
        topic = q.get('_source_topic', 'Unknown')
        if topic not in topics:
            topics[topic] = 0
        topics[topic] += 1
    
    return topics


def main():
    parser = argparse.ArgumentParser(
        description='Parse HTML files and extract questions for StudyPulse import'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to the input HTML file'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to the output JSON file'
    )
    parser.add_argument(
        '--topic-map', '-t',
        default='{}',
        help='JSON string mapping topic names to IDs (e.g., \'{"Topic Name": 1}\')'
    )
    parser.add_argument(
        '--default-topic', '-d',
        type=int,
        default=1,
        help='Default topic ID for unmapped topics (default: 1)'
    )
    parser.add_argument(
        '--no-images',
        action='store_true',
        help='Exclude image URLs from output'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate a topic mapping report'
    )
    
    args = parser.parse_args()
    
    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    logger.info(f"Reading input file: {args.input}")
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse topic map
    try:
        topic_id_map = json.loads(args.topic_map)
    except json.JSONDecodeError:
        logger.warning("Invalid topic map JSON, using empty map")
        topic_id_map = {}
    
    # Parse HTML
    parser_instance = QuestionHTMLParser(html_content, source_name=input_path.stem)
    raw_questions = parser_instance.parse()
    
    if not raw_questions:
        logger.error("No questions found in the HTML file")
        return 1
    
    # Generate topic report if requested
    if args.report:
        topics = generate_topic_mapping_report(raw_questions)
        logger.info("\n=== Topic Mapping Report ===")
        for topic, count in sorted(topics.items()):
            logger.info(f"  {topic}: {count} questions")
        logger.info(f"\nTotal: {len(raw_questions)} questions")
        
        # Save report
        report_path = Path(args.output).with_suffix('.report.json')
        with open(report_path, 'w') as f:
            json.dump({
                "topics": topics,
                "total_questions": len(raw_questions),
                "topic_map_template": {t: None for t in topics.keys()}
            }, f, indent=2)
        logger.info(f"Saved topic report to {report_path}")
    
    # Transform questions
    transformed = parser_instance.transform_for_import(
        raw_questions,
        topic_id_map=topic_id_map,
        default_topic_id=args.default_topic
    )
    
    # Generate output
    generate_import_json(
        transformed,
        args.output,
        include_images=not args.no_images
    )
    
    logger.info("✅ Parsing complete!")
    return 0


if __name__ == "__main__":
    exit(main())
