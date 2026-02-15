"""Web scraper for NEET PG question websites.

Scrapes MCQ questions from popular NEET PG preparation websites:
- Marrow.in
- PrepLadder
- DAMS NEET PG
- Medscape MCQs
- Other NEET PG question banks

Extracts questions, options, answers, and explanations.
"""
import asyncio
import logging
import re
from typing import List, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from app.schemas.question_import import QuestionImport

logger = logging.getLogger(__name__)


class NEETQuestionScraper:
    """Scrapes NEET PG MCQ questions from various websites."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Popular NEET PG question websites
    NEET_WEBSITES = {
        "marrow": {
            "base_url": "https://www.marrow.in",
            "patterns": [
                "/qbank/",
                "/grand-tests/",
                "/daily-quiz/"
            ]
        },
        "prepladder": {
            "base_url": "https://www.prepladder.com",
            "patterns": [
                "/neet-pg/questions/",
                "/practice-mcqs/"
            ]
        },
        "medscape": {
            "base_url": "https://www.medscape.com",
            "patterns": [
                "/quiz/",
                "/viewarticle/"
            ]
        },
    }

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers={"User-Agent": self.USER_AGENT}
            )

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def scrape_url(
        self,
        url: str,
        topic_id: int,
        source_name: str = "WEB",
        max_questions: int = 50
    ) -> List[QuestionImport]:
        """Scrape questions from a single URL.

        Args:
            url: URL to scrape
            topic_id: Database topic ID
            source_name: Source identifier
            max_questions: Maximum questions to extract

        Returns:
            List of QuestionImport objects
        """
        await self.initialize()

        try:
            logger.info(f"Scraping NEET: {url}")
            resp = await self._client.get(url)
            resp.raise_for_status()

            html = resp.text
            soup = BeautifulSoup(html, 'lxml')

            questions = []

            # Strategy 1: Generic medical MCQ pattern
            questions.extend(self._parse_generic_medical_mcq(soup, topic_id, source_name))

            # Strategy 2: Marrow specific
            if "marrow.in" in url:
                questions.extend(self._parse_marrow(soup, topic_id, source_name))

            # Strategy 3: Medscape specific
            if "medscape.com" in url:
                questions.extend(self._parse_medscape(soup, topic_id, source_name))

            logger.info(f"Scraped {len(questions)} NEET questions from {url}")
            return questions[:max_questions]

        except Exception as e:
            logger.error(f"Failed to scrape NEET {url}: {e}")
            return []

    def _parse_generic_medical_mcq(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Generic medical MCQ parser."""
        questions = []

        # Medical MCQs often have specific patterns
        question_containers = soup.find_all(
            ['div', 'section', 'article'],
            class_=re.compile(r'question|quiz|mcq|qbank', re.I)
        )

        for container in question_containers:
            try:
                # Extract question text
                question_elem = container.find(
                    ['p', 'h3', 'h4', 'div'],
                    class_=re.compile(r'question-text|question-stem|quiz-question', re.I)
                )

                if not question_elem:
                    # Try finding by text pattern (e.g., "Q1.", "Question 1:")
                    question_elem = container.find(
                        string=re.compile(r'^(Q\d+|Question\s+\d+)[:.]\s*', re.I)
                    )

                if not question_elem:
                    continue

                question_text = self._clean_text(question_elem.get_text())

                # Remove question number prefix
                question_text = re.sub(r'^(Q\d+|Question\s+\d+)[:.]\s*', '', question_text, flags=re.I)

                if not question_text or len(question_text) < 20:
                    continue

                # Extract options
                options_dict = {}
                option_elems = container.find_all(
                    ['li', 'div', 'p'],
                    class_=re.compile(r'option|choice|answer-option', re.I)
                )

                for opt in option_elems[:4]:
                    opt_text = self._clean_text(opt.get_text())
                    # Medical MCQs often use (a), (b), (c), (d) or A., B., C., D.
                    match = re.match(r'^[(\[]?([A-Da-d])[)\].:]\s*(.+)', opt_text)
                    if match:
                        label, text = match.groups()
                        options_dict[label.upper()] = text.strip()

                if len(options_dict) != 4:
                    # Try alternative pattern: option might be span + text
                    options_dict = self._extract_options_alternative(container)

                if len(options_dict) != 4:
                    continue

                # Extract correct answer
                correct_answer = None

                # Method 1: Look for class="correct" or data-correct
                for idx, opt_elem in enumerate(option_elems[:4]):
                    if 'correct' in ' '.join(opt_elem.get('class', [])).lower():
                        correct_answer = chr(65 + idx)  # A, B, C, D
                        break

                # Method 2: Look for answer section
                if not correct_answer:
                    answer_elem = container.find(
                        ['span', 'div', 'p'],
                        class_=re.compile(r'answer|correct|solution', re.I)
                    )
                    if answer_elem:
                        answer_text = self._clean_text(answer_elem.get_text())
                        for letter in ['A', 'B', 'C', 'D']:
                            if letter in answer_text.upper():
                                correct_answer = letter
                                break

                if not correct_answer:
                    continue

                # Extract explanation
                explanation = None
                expl_elem = container.find(
                    ['div', 'p', 'section'],
                    class_=re.compile(r'explanation|solution|rationale|discussion', re.I)
                )
                if expl_elem:
                    explanation = self._clean_text(expl_elem.get_text())[:500]

                # Create question
                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    source=source,
                    year=None,
                    difficulty="medium"
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse medical MCQ: {e}")
                continue

        return questions

    def _parse_marrow(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Parse Marrow.in specific question format."""
        questions = []

        # Marrow uses React/dynamic content, so this is a basic parser
        # For full scraping, use Playwright/Selenium

        question_blocks = soup.find_all('div', class_=re.compile(r'question-card|qbank-item'))

        for block in question_blocks:
            try:
                # Question text
                q_elem = block.find(['div', 'p'], class_=re.compile(r'question-stem|question-text'))
                if not q_elem:
                    continue

                question_text = self._clean_text(q_elem.get_text())

                # Options
                options_list = block.find('ul', class_=re.compile(r'options|choices'))
                if not options_list:
                    options_list = block.find_all('li', class_=re.compile(r'option'))

                options_dict = {}
                if isinstance(options_list, list):
                    for idx, li in enumerate(options_list[:4]):
                        label = chr(65 + idx)
                        text = self._clean_text(li.get_text())
                        options_dict[label] = text
                else:
                    for idx, li in enumerate(options_list.find_all('li')[:4]):
                        label = chr(65 + idx)
                        text = self._clean_text(li.get_text())
                        options_dict[label] = text

                if len(options_dict) != 4:
                    continue

                # Correct answer
                correct_answer = None
                answer_elem = block.find(attrs={'data-correct': True})
                if answer_elem:
                    correct_idx = answer_elem.get('data-correct-index')
                    if correct_idx:
                        try:
                            correct_answer = chr(65 + int(correct_idx))
                        except (ValueError, TypeError):
                            pass

                if not correct_answer:
                    # Look in explanation section
                    expl_elem = block.find(['div', 'p'], class_=re.compile(r'explanation|answer'))
                    if expl_elem:
                        expl_text = expl_elem.get_text().upper()
                        for letter in ['A', 'B', 'C', 'D']:
                            if f'ANSWER: {letter}' in expl_text or f'ANS: {letter}' in expl_text:
                                correct_answer = letter
                                break

                if not correct_answer:
                    continue

                # Explanation
                explanation = None
                expl_elem = block.find(['div', 'section'], class_=re.compile(r'explanation|discussion'))
                if expl_elem:
                    explanation = self._clean_text(expl_elem.get_text())[:500]

                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    source=f"WEB: Marrow - {source}",
                    year=None,
                    difficulty="medium"
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse Marrow question: {e}")
                continue

        return questions

    def _parse_medscape(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Parse Medscape specific question format."""
        questions = []

        # Medscape MCQs typically in quiz format
        quiz_questions = soup.find_all('div', class_=re.compile(r'quiz-question|question-block'))

        for block in quiz_questions:
            try:
                # Question text
                q_elem = block.find(['p', 'div'], class_=re.compile(r'question-text|stem'))
                if not q_elem:
                    continue

                question_text = self._clean_text(q_elem.get_text())

                # Options
                options_dict = {}
                radio_buttons = block.find_all('input', type='radio')

                for radio in radio_buttons[:4]:
                    label_elem = radio.find_next('label')
                    if label_elem:
                        label_text = self._clean_text(label_elem.get_text())
                        # Extract letter and text
                        match = re.match(r'^([A-D])[).:\s]+(.+)', label_text)
                        if match:
                            letter, text = match.groups()
                            options_dict[letter.upper()] = text.strip()

                if len(options_dict) != 4:
                    continue

                # Correct answer
                correct_answer = None
                for radio in radio_buttons:
                    if radio.get('data-correct') == 'true' or 'correct' in radio.get('class', []):
                        value = radio.get('value', '')
                        if value in ['A', 'B', 'C', 'D']:
                            correct_answer = value
                            break

                if not correct_answer:
                    continue

                # Explanation
                explanation = None
                expl_elem = block.find(['div', 'section'], class_=re.compile(r'explanation|rationale'))
                if expl_elem:
                    explanation = self._clean_text(expl_elem.get_text())[:500]

                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    source=f"WEB: Medscape - {source}",
                    year=None,
                    difficulty="medium"
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse Medscape question: {e}")
                continue

        return questions

    def _extract_options_alternative(self, container) -> Dict[str, str]:
        """Alternative method to extract options when standard parsing fails."""
        options = {}

        # Method 1: Look for <label> tags with option text
        labels = container.find_all('label')
        for label in labels[:4]:
            text = self._clean_text(label.get_text())
            match = re.match(r'^[(\[]?([A-Da-d])[)\].:]\s*(.+)', text)
            if match:
                letter, option_text = match.groups()
                options[letter.upper()] = option_text.strip()

        if len(options) == 4:
            return options

        # Method 2: Look for consecutive <p> or <div> with option pattern
        all_elems = container.find_all(['p', 'div'])
        for elem in all_elems:
            text = self._clean_text(elem.get_text())
            match = re.match(r'^[(\[]?([A-Da-d])[)\].:]\s*(.+)', text)
            if match and len(options) < 4:
                letter, option_text = match.groups()
                if letter.upper() not in options:
                    options[letter.upper()] = option_text.strip()

        return options

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Remove HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#039;', "'")
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')

        return text

    async def scrape_multiple_urls(
        self,
        urls: List[str],
        topic_id: int,
        max_questions_per_url: int = 20
    ) -> List[QuestionImport]:
        """Scrape multiple URLs concurrently."""
        await self.initialize()

        tasks = [
            self.scrape_url(url, topic_id, f"NEET_URL_{idx}", max_questions_per_url)
            for idx, url in enumerate(urls, 1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_questions = []
        for result in results:
            if isinstance(result, list):
                all_questions.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"NEET scraping failed: {result}")

        return all_questions


# Singleton
neet_scraper = NEETQuestionScraper()
