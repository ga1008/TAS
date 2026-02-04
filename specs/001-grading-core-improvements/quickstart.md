# Quick Start Guide: Grading Core Improvements

**Feature**: 001-grading-core-improvements
**Date**: 2026-02-03
**Phase**: 1 - Design & Contracts

## Overview

This guide helps you use the new features for grading core improvements:
1. **Extra Prompt for Logic Cores**: Provide additional guidance to AI when generating Python graders
2. **Fixed AI Direct Cores**: AI direct cores now properly handle images, videos, and PDFs

---

## Feature 1: Extra Prompt for Logic Cores

### What Is It?

When generating a logic core (Python grader), you can now provide an **extra prompt** to guide the AI. This helps with:
- File name matching (handle typos, variations)
- Edge cases specific to your assignment
- Custom grading preferences

### How to Use

1. **Navigate to AI Generator**
   - Go to `/ai_generator` in your browser
   - Log in with your teacher account

2. **Fill in the Form**
   - Enter **Task Name** (e.g., "Python Advanced Final 2025")
   - Select **Exam File** (upload exam document)
   - Select **Standard File** (upload grading rubric)
   - Choose **Strictness** (loose/standard/strict)

3. **Add Extra Prompt** (Optional but Recommended)
   - Locate the "Extra Prompt" textarea
   - Enter your additional guidance
   - See examples below

4. **Submit**
   - Click "Generate Grader" button
   - Wait for AI to generate the Python code
   - View results in AI Core List

### Extra Prompt Examples

#### Example 1: Handle File Name Typos

```
Students often make typos in file names. Please handle these variations:
- test1.py might be test01.py, test_1.py, or Test1.py
- main.py could be Main.py, MAIN.py, or main1.py
- utils.py might be util.py, utility.py, or helpers.py

Try to find files using flexible matching.
```

#### Example 2: Handle Missing Files

```
If a student forgets to submit a required file:
- Don't fail the entire assignment
- Deduct partial points for the missing file
- Continue grading other files
- Add a clear deduction message
```

#### Example 3: Custom Grading Logic

```
For this assignment:
- Priority is on code correctness over style
- Comments are optional but appreciated
- Partial credit should be given for incomplete implementations
- Focus on the algorithm, not the output format
```

#### Example 4: Multiple File Requirements

```
Students should submit:
1. A main script (any name is OK)
2. At least one test file
3. A README.md (optional)

If they submit multiple main scripts, grade the most recently modified one.
```

### Tips for Writing Extra Prompts

✅ **DO**:
- Be specific about what you want
- Provide examples of file name variations
- Explain grading preferences clearly
- Keep under 2000 characters (soft limit)
- Use clear, concise language

❌ **DON'T**:
- Don't repeat information already in exam/standard files
- Don't write entire grading logic (AI will generate it)
- Don't exceed 2000 characters without good reason
- Don't use ambiguous language

### Character Limit

- **Soft Limit**: 2000 characters
- **Behavior**: Shows warning if exceeded, but allows submission
- **Recommendation**: Keep it brief and focused

---

## Feature 2: Fixed AI Direct Cores

### What Is It?

AI direct cores can now properly handle:
- **Images** (JPG, PNG, JPEG, GIF, etc.) - converted to base64
- **Videos** (MP4, AVI, MOV) - uploaded via Volcengine Files API
- **PDFs** - uploaded via Volcengine Files API

### What Changed

**Before**:
- AI direct cores would crash when processing images/videos/PDFs
- Runtime errors due to incorrect API format

**After**:
- Images are automatically converted to base64 format
- Videos and PDFs are uploaded to Volcengine cloud
- All file types are processed correctly
- Failed files are skipped with warnings

### How to Use

No changes to workflow! AI direct cores now work correctly:

1. **Create AI Direct Grader**
   - Go to `/ai_generator`
   - Click "Direct Mode" tab
   - Fill in form (task name, exam, standard, extra instructions)

2. **Upload Student Submissions**
   - Students submit assignments as ZIP files
   - System extracts automatically

3. **Run Grading**
   - Click "Run Auto Grading" button
   - System processes images, videos, and PDFs automatically
   - View results in class overview

### Supported File Types

| Type | Formats | Processing | Limit |
|------|---------|------------|-------|
| **Images** | JPG, PNG, JPEG, GIF, WebP, BMP, TIFF, HEIC | Base64 encoding | 5 MB per image |
| **Videos** | MP4, AVI, MOV | Files API upload | 512 MB per video |
| **PDFs** | PDF | Files API upload | 512 MB per PDF |
| **Code** | PY, JAVA, C, CPP, HTML, CSS, JS, etc. | Text extraction | 10 MB per file |
| **Documents** | DOC, DOCX, TXT, MD | Text extraction | 10 MB per file |

### File Limits

| Limit Type | Count | Behavior |
|------------|-------|----------|
| **Soft Limit** | 5 media files | Show warning, continue |
| **Hard Limit** | 10 media files | Reject submission |
| **File Size** | 512 MB | Skip file with warning |

### Error Handling

The system now handles errors gracefully:

```
[Processing student submission...]
✓ Found: main.py
✓ Found: test_output.png (converted to base64)
✓ Found: demo_video.mp4 (uploaded to Volcengine)
✓ Found: requirements.pdf (uploaded to Volcengine)
⚠ Skipping: huge_file.mp4 (exceeds 512 MB limit)
⚠ Skipping: corrupted.png (encoding failed)

Grading complete with 4 files processed.
```

---

## Troubleshooting

### Extra Prompt Issues

**Problem**: Extra prompt not being used by AI

**Solutions**:
1. Verify prompt text is clear and specific
2. Check that prompt is under 2000 characters
3. Try regenerating the grader with simplified prompt
4. Check task log for AI generation errors

**Problem**: Character count not showing

**Solutions**:
1. Refresh the page
2. Clear browser cache
3. Check browser console for JavaScript errors

### AI Direct Core Issues

**Problem**: Images still causing errors

**Solutions**:
1. Verify image format is supported (JPG, PNG, etc.)
2. Check image size is under 5 MB
3. Ensure Volcengine API credentials are configured
4. Check AI model supports "vision" capability

**Problem**: Videos not processing

**Solutions**:
1. Verify video format: MP4, AVI, or MOV
2. Check video size is under 512 MB
3. Ensure stable internet connection for upload
4. Wait longer for video upload (may take 1-2 minutes)

**Problem**: "No vision-capable AI model configured"

**Solutions**:
1. Go to `/admin` panel
2. Add AI provider (Volcengine or OpenAI-compatible)
3. Add model with "vision" capability
4. Ensure model has `capability = "vision"` in database

---

## Examples

### Complete Workflow: Logic Core with Extra Prompt

```
1. Teacher prepares exam.docx and standard.pdf
2. Teacher goes to /ai_generator
3. Teacher fills form:
   - Task Name: "Python Final Exam 2025"
   - Exam: exam.docx
   - Standard: standard.pdf
   - Strictness: standard
   - Extra Prompt:
     "Students may have typos in filenames:
     - lab1.py → lab01.py or Lab1.py
     - main.py → Main.py
     Try to match files flexibly."
4. Teacher clicks "Generate Grader"
5. AI generates Python grader code
6. Teacher views generated code in AI Core List
7. Teacher creates class, uploads student ZIP files
8. System runs grader on each submission
9. Results show in class overview
```

### Complete Workflow: AI Direct Core with Mixed Media

```
1. Teacher creates direct grader for video assignment
2. Students submit ZIP files containing:
   - demo.mp4 (video demonstration)
   - screenshot.png (result image)
   - code.py (source code)
   - README.md (documentation)
3. System processes submission:
   - demo.mp4 → Uploaded to Volcengine Files API
   - screenshot.png → Converted to base64
   - code.py → Extracted as text
   - README.md → Extracted as text
4. AI analyzes all content and returns scores
5. Results include detailed feedback for each file
```

---

## FAQ

### Q: Can I use both extra prompt and strictness?

**A**: Yes! They work together:
- **Strictness** controls overall grading strictness (loose/standard/strict)
- **Extra Prompt** provides specific guidance for file matching and edge cases

### Q: What happens if I don't provide an extra prompt?

**A**: The system works exactly as before. The extra prompt is optional and enhances but doesn't replace the standard generation process.

### Q: Can I edit the extra prompt after generating the grader?

**A**: No, you would need to regenerate the grader with the updated prompt. However, you can manually edit the generated Python code if needed.

### Q: Do I need to change my existing AI direct cores?

**A**: No! The fix is in the template. New AI direct cores will work correctly. Existing cores can be regenerated if needed.

### Q: Will extra prompts increase AI costs?

**A**: Possibly, because longer prompts use more tokens. However, the 2000 character soft limit helps control costs. You'll see a warning if exceeded.

### Q: What happens if a student submits more than 10 media files?

**A**: The system will reject the submission with an error message. The teacher should ask the student to reduce the number of files or combine them.

---

## Support

For issues or questions:
1. Check this guide first
2. View task logs in AI Core List
3. Check browser console for JavaScript errors
4. Contact system administrator

---

## References

- [Feature Specification](./spec.md) - Full requirements
- [API Contracts](./contracts/api.md) - API documentation
- [Data Model](./data-model.md) - Database schema
- [Research Findings](./research.md) - Technical details
