"""Web scraper for UPSC question websites.

Scrapes MCQ questions from popular UPSC preparation websites:
- ClearIAS.com
- InsightsOnIndia
- Vision IAS
- Shankar IAS Academy
- Other UPSC question banks

Extracts questions, options, answers, and explanations.
"""
import asyncio
import logging
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.schemas.question_import import QuestionImport

logger = logging.getLogger(__name__)


class UPSCQuestionScraper:
    """Scrapes UPSC MCQ questions from various websites."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Popular UPSC question websites
    UPSC_WEBSITES = {
        "clearias": {
            "base_url": "https://www.clearias.com",
            "patterns": [
                "/upsc-prelims-questions/",
                "/current-affairs/",
                "/daily-current-affairs-quiz/",
            ]
        },
        "insights": {
            "base_url": "https://www.insightsonindia.com",
            "patterns": [
                "/secure-synopsis/",
                "/daily-quiz/"
            ]
        },
        "vision_ias": {
            "base_url": "https://www.visionias.in",
            "patterns": [
                "/current-affairs/",
                "/daily-current-affairs-quiz/"
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
            logger.info(f"Scraping: {url}")
            resp = await self._client.get(url)
            resp.raise_for_status()

            html = resp.text
            soup = BeautifulSoup(html, 'lxml')

            # Try different parsing strategies
            questions = []

            # Strategy 1: Generic MCQ pattern matching
            questions.extend(self._parse_generic_mcq(soup, topic_id, source_name))

            # Strategy 2: ClearIAS specific
            if "clearias.com" in url:
                questions.extend(self._parse_clearias(soup, topic_id, source_name))

            # Strategy 3: InsightsOnIndia specific
            if "insightsonindia.com" in url:
                questions.extend(self._parse_insights(soup, topic_id, source_name))

            logger.info(f"Scraped {len(questions)} questions from {url}")
            return questions[:max_questions]

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return []

    def _parse_generic_mcq(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Generic MCQ parser - works for most question formats.

        Looks for common patterns:
        - Question text followed by options A/B/C/D
        - Answer indicator
        - Optional explanation
        """
        questions = []

        # Find all divs/sections that might contain MCQs
        question_containers = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'question|quiz|mcq', re.I))

        for container in question_containers:
            try:
                # Extract question text
                question_elem = container.find(['p', 'h3', 'h4', 'div'], class_=re.compile(r'question-text|quiz-question', re.I))
                if not question_elem:
                    continue

                question_text = self._clean_text(question_elem.get_text())
                if not question_text or len(question_text) < 20:
                    continue

                # Extract options
                options_dict = {}
                option_elems = container.find_all(['li', 'div', 'p'], class_=re.compile(r'option|choice', re.I))

                for opt in option_elems[:4]:  # Max 4 options
                    opt_text = self._clean_text(opt.get_text())
                    # Try to extract option label (A, B, C, D)
                    match = re.match(r'^([A-D])[).:\s]+(.+)', opt_text)
                    if match:
                        label, text = match.groups()
                        options_dict[label.upper()] = text.strip()

                if len(options_dict) != 4:
                    continue  # Need exactly 4 options

                # Extract correct answer
                answer_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'answer|correct', re.I))
                correct_answer = None

                if answer_elem:
                    answer_text = self._clean_text(answer_elem.get_text())
                    # Try to extract A/B/C/D
                    for letter in ['A', 'B', 'C', 'D']:
                        if letter in answer_text.upper():
                            correct_answer = letter
                            break

                if not correct_answer:
                    continue  # Must have correct answer

                # Extract explanation (optional)
                explanation_elem = container.find(['div', 'p'], class_=re.compile(r'explanation|solution', re.I))
                explanation = None
                if explanation_elem:
                    explanation = self._clean_text(explanation_elem.get_text())[:500]  # Max 500 chars

                # Create question object
                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    source=source,
                    year=None,
                    difficulty="medium"  # Default
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse question container: {e}")
                continue

        return questions

    def _parse_clearias(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Parse ClearIAS specific question format.

        ClearIAS typically uses:
        - <div class="wpProQuiz_question">
        - <li class="wpProQuiz_questionListItem">
        """
        questions = []

        question_blocks = soup.find_all('div', class_=re.compile(r'wpProQuiz|quiz-question'))

        for block in question_blocks:
            try:
                # Question text
                q_text_elem = block.find('div', class_=re.compile(r'wpProQuiz_question_text|question-text'))
                if not q_text_elem:
                    continue

                question_text = self._clean_text(q_text_elem.get_text())

                # Options
                option_list = block.find('ul', class_=re.compile(r'wpProQuiz_list|answer-list'))
                if not option_list:
                    continue

                options_dict = {}
                for idx, li in enumerate(option_list.find_all('li')[:4]):
                    label = chr(65 + idx)  # A, B, C, D
                    text = self._clean_text(li.get_text())
                    options_dict[label] = text

                if len(options_dict) != 4:
                    continue

                # Correct answer (often in data attribute)
                correct_answer = None
                for idx, li in enumerate(option_list.find_all('li')[:4]):
                    if 'wpProQuiz_answerCorrect' in li.get('class', []) or \
                       'correct' in li.get('class', []):
                        correct_answer = chr(65 + idx)
                        break

                if not correct_answer:
                    # Try data-pos attribute
                    correct_pos = block.get('data-question-correct-pos')
                    if correct_pos:
                        try:
                            correct_answer = chr(65 + int(correct_pos))
                        except:
                            pass

                if not correct_answer:
                    continue

                # Explanation
                explanation = None
                expl_elem = block.find('div', class_=re.compile(r'wpProQuiz_response|explanation'))
                if expl_elem:
                    explanation = self._clean_text(expl_elem.get_text())[:500]

                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    source=f"WEB: ClearIAS - {source}",
                    year=None,
                    difficulty="medium"
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse ClearIAS question: {e}")
                continue

        return questions

    def _parse_insights(
        self, soup: BeautifulSoup, topic_id: int, source: str
    ) -> List[QuestionImport]:
        """Parse InsightsOnIndia specific question format."""
        # Similar to generic parser but with Insights-specific selectors
        questions = []

        # InsightsOnIndia typically uses numbered questions
        question_blocks = soup.find_all(['div', 'p'], string=re.compile(r'^\d+\.\s+'))

        for block in question_blocks:
            try:
                # Extract question number and text
                full_text = self._clean_text(block.get_text())
                match = re.match(r'^\d+\.\s+(.+)', full_text)
                if not match:
                    continue

                question_text = match.group(1)

                # Find next 4 sibling elements (options)
                options_dict = {}
                current = block.find_next_sibling()
                option_count = 0

                while current and option_count < 4:
                    opt_text = self._clean_text(current.get_text())
                    match = re.match(r'^([a-d])[).:\s]+(.+)', opt_text, re.I)
                    if match:
                        label, text = match.groups()
                        options_dict[label.upper()] = text.strip()
                        option_count += 1

                    current = current.find_next_sibling()

                if len(options_dict) != 4:
                    continue

                # Look for answer in next few elements
                correct_answer = None
                check_elem = current
                for _ in range(5):  # Check next 5 elements
                    if check_elem:
                        text = check_elem.get_text().upper()
                        if 'ANSWER' in text or 'ANS' in text:
                            for letter in ['A', 'B', 'C', 'D']:
                                if letter in text:
                                    correct_answer = letter
                                    break
                            break
                        check_elem = check_elem.find_next_sibling()

                if not correct_answer:
                    continue

                question = QuestionImport(
                    topic_id=topic_id,
                    question_text=question_text,
                    options=options_dict,
                    correct_answer=correct_answer,
                    explanation=None,
                    source=f"WEB: InsightsOnIndia - {source}",
                    year=None,
                    difficulty="medium"
                )
                questions.append(question)

            except Exception as e:
                logger.debug(f"Failed to parse Insights question: {e}")
                continue

        return questions

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#039;', "'")

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
            self.scrape_url(url, topic_id, f"URL_{idx}", max_questions_per_url)
            for idx, url in enumerate(urls, 1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_questions = []
        for result in results:
            if isinstance(result, list):
                all_questions.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping failed: {result}")

        return all_questions


# Singleton
upsc_scraper = UPSCQuestionScraper()
