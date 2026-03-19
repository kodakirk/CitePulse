# CitePulse - User Guide

CitePulse analyzes how a scientific paper has been cited by other researchers to determine whether the broader scientific community supports, extends, or refutes its findings.

---

## Accessing CitePulse

Open a web browser on any device connected to the same network as the server and go to:

```
http://<server-ip>:8501
```

Replace `<server-ip>` with the IP address of the machine running CitePulse (ask your server administrator for this).

Example: `http://192.168.1.50:8501`

CitePulse works in any modern browser (Chrome, Firefox, Edge, Safari) on desktop or mobile.

---

## Creating an account

An account is optional for basic analysis, but required to save your search history.

1. Click **Sign up** in the top-right corner.
2. Enter your full name, email address, and a password (minimum 6 characters).
3. Click **Create Account**.
4. You will be redirected to the login page. Enter your email and password, then click **Login**.

---

## Analyzing a paper

### 1. Choose a search method

Select one of two options at the top of the page:

- **Paper ID (arXiv/DOI)** — Enter an arXiv ID or DOI directly.
  - arXiv example: `1706.03762`
  - DOI example: `10.1038/s41586-020-2649-2`

- **Paper Title** — Enter the title of the paper and CitePulse will search for it.
  - Example: `Attention is All You Need`

### 2. (Optional) Configure advanced options

Click **Advanced Options** to expand the settings panel.

#### Number of papers to analyze

Use the slider to choose how many citing papers to include (10–50). More papers give a more complete picture but take longer to process.

#### Temporal weighting

Control whether recent or older citations carry more weight in the consensus score:

| Option                  | Effect                                                    |
|-------------------------|-----------------------------------------------------------|
| Favor newer research    | Recent citations count more heavily (default)             |
| Favor older research    | Established, older citations count more heavily           |
| No temporal bias        | All citations are weighted equally regardless of age      |

When temporal bias is enabled, the **strength slider** (0.01–0.20) controls how aggressively the weighting is applied. Higher values create a stronger bias.

#### Authorship bias

When **Reduce weight for self-citations** is checked, citations authored by the same people who wrote the original paper receive less weight. This prevents authors from artificially inflating their own consensus scores.

The **penalty slider** controls severity:
- `0.0` = self-citations are completely ignored
- `0.5` = self-citations count at half weight (default)
- `1.0` = no penalty (self-citations treated normally)

#### Category filters

Check or uncheck categories to control which types of citations appear in the results:

- **Support** — Papers that confirm or validate the original findings
- **Extend** — Papers that build upon the original work in new directions
- **Neutral** — Papers that reference the work without taking a position
- **Refute** — Papers that contradict or challenge the original findings

### 3. Run the analysis

Click **Analyze Paper**. The analysis typically takes 30 seconds to 2 minutes depending on the number of citations and server load.

---

## Reading the results

### Retracted papers

If the paper has been officially retracted (withdrawn from the scientific record), CitePulse displays a prominent warning and does not perform further analysis. Retracted papers should not be cited.

### Consensus metrics

Five cards are displayed at the top of the results:

| Metric      | Meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| **Support** | Number of citing papers that confirm the original findings              |
| **Extend**  | Number of citing papers that build on the work                          |
| **Neutral** | Number of citing papers that reference it without taking a position     |
| **Refute**  | Number of citing papers that contradict the findings                    |
| **Consensus** | Overall consensus score (see below)                                  |

#### How the consensus score is calculated

Each citation contributes to the score based on its classification:

- Support = +1.0
- Extend = +0.5
- Neutral = 0.0
- Refute = -1.0

The score is the weighted sum of contributions divided by the total weight, normalized to a 0–1 scale. A score near **1.0** means strong agreement; near **0.0** means strong disagreement; near **0.5** means mixed or neutral reception.

### Citation trend analysis

Below the metrics, a trend panel shows how citation patterns have changed over time:

- **Trending Up** — The paper is receiving more citations recently than in the past
- **Stable** — Citation rate has remained consistent
- **Declining** — The paper is receiving fewer citations recently

The **momentum score** shows the ratio of recent citation rate (last 3 years) to historical rate. A value of `1.5x` means the paper is being cited 50% more frequently now than it was historically.

### Timeline chart

An interactive scatter plot shows citations over time, color-coded by category:

- Green = Support
- Blue = Extend
- Gray = Neutral
- Red = Refute

Hover over points to see details. This visualization helps identify whether sentiment is shifting over time (e.g., early support followed by later refutations).

### Citations by category

Expandable sections list every analyzed citation, grouped by category. Each entry shows:

- **Title** — The citing paper's title
- **Classification** — Support, Extend, Neutral, or Refute, with a confidence score (0.00–1.00)
- **Year** — When the citing paper was published
- **Explanation** — Why the AI classified this citation the way it did
- **Snippet** — The relevant passage from the citing paper

---

## Search history

When logged in, your past analyses are saved and displayed in the left sidebar under **Search History**.

- Each entry shows the paper title (or ID), the date of the analysis, and the consensus score.
- Click any history entry to pre-fill the paper ID in the search box for quick re-analysis.
- Up to 20 recent analyses are shown in the sidebar.

---

## Tips for best results

1. **Use paper IDs when possible.** arXiv IDs and DOIs give exact matches. Title search may occasionally find the wrong paper if the title is generic.

2. **Start with 20 papers** (the default). Increase to 50 only if you want a more comprehensive analysis — it will take longer.

3. **Check the confidence scores.** A classification with confidence below 0.5 means the AI was uncertain. Read the explanation and snippet to judge for yourself.

4. **Enable self-citation reduction** for a more objective consensus score. Authors frequently cite their own prior work, which can skew results.

5. **Use temporal weighting** to focus on current scientific opinion. A paper may have been widely supported in 2015 but challenged by newer research in 2024.

6. **Look at the trend chart.** A high consensus score with a declining trend may indicate that the community is starting to question the findings.

---

## Frequently asked questions

**Q: Do I need an account to use CitePulse?**
A: No. You can analyze papers without logging in. However, creating an account enables search history so you can revisit past analyses.

**Q: Where does CitePulse get its data?**
A: Paper metadata and citation data come from the Semantic Scholar academic database. Citation classification (support, refute, etc.) is performed by an AI language model (Mistral).

**Q: How accurate is the classification?**
A: The AI provides a confidence score for each classification. High-confidence results (above 0.8) are generally reliable. For critical research decisions, always read the cited passages yourself.

**Q: Why did my analysis return fewer papers than I requested?**
A: Some papers have few citations, or some citing papers may lack accessible abstracts. CitePulse only classifies citations where it has enough text to make a determination.

**Q: What does "Consensus: 0.000" mean?**
A: A score of exactly 0.000 usually means all analyzed citations were neutral — none clearly supported or refuted the paper.

**Q: Can I analyze papers from any field?**
A: Yes. CitePulse works with any paper indexed by Semantic Scholar, which covers computer science, medicine, biology, physics, social sciences, and more.

**Q: The analysis is taking a long time. Is that normal?**
A: Analyses of 20 papers typically complete in 30–90 seconds. Larger analyses (50 papers) can take up to 3 minutes. If it takes longer, the server may be under heavy load.
