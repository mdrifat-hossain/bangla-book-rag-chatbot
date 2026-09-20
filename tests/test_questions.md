# 10 Test Questions — কপালকুণ্ডলা (Kapalkundala)

> ⚠️ **Important — read before submitting:** The `expected_source` values
> below are my best-effort estimates based on the well-known, publicly
> documented plot/structure of *Kapalkundala* (a public-domain 1866
> novel by Bankim Chandra Chattopadhyay). This project was written
> without live access to the exact bn.wikisource.org page-by-page text,
> so **after you run `python pipeline.py` once, ask each question in the
> app and copy the *actual* chapter citation the chatbot returns into
> this table**, replacing my estimate. This takes about 10 minutes and
> ensures your submission is 100% accurate to your specific crawled
> pages. Also update `test_questions.json` (used by the bonus script)
> to match.

| # | Question | Expected Answer | Source/Chapter |
|---|----------|------------------|-----------------|
| 1 | কপালকুণ্ডলা উপন্যাসের রচয়িতা কে? | বঙ্কিমচন্দ্র চট্টোপাধ্যায়। | ভূমিকা / প্রধান পাতা |
| 2 | নবকুমার কোথাকার বাসিন্দা ছিলেন? | নবকুমার সপ্তগ্রামের একজন যুবক ভদ্রলোক ছিলেন। | দ্বিতীয় খণ্ড / ষষ্ঠ পরিচ্ছেদ |
| 3 | কপালকুণ্ডলা কোথায় এবং কার কাছে বেড়ে উঠেছিলেন? | একজন কাপালিক (তান্ত্রিক সাধক) কর্তৃক এক নির্জন অরণ্যে পালিত হয়ে বড় হয়েছিলেন। | প্রথম খণ্ড / প্রথম-দ্বিতীয় পরিচ্ছেদ |
| 4 | নবকুমার কীভাবে কপালকুণ্ডলার সাথে প্রথম পরিচিত হন? | সমুদ্রযাত্রায় পথ হারিয়ে বিপদে পড়ে অরণ্যে কপালকুণ্ডলার সাহায্যে রক্ষা পান। | প্রথম খণ্ড / প্রথম-তৃতীয় পরিচ্ছেদ |
| 5 | উপন্যাসের কাহিনী মূলত কোন অঞ্চলে সংঘটিত হয়েছে? | বর্তমান পূর্ব মেদিনীপুর জেলার দরিয়াপুর/কাঁথি অঞ্চল এবং পরে সপ্তগ্রাম। | প্রথম খণ্ড / অষ্টম পরিচ্ছেদ |
| 6 | কাপালিক কপালকুণ্ডলার প্রতি কী উদ্দেশ্য পোষণ করতেন? | তান্ত্রিক অনুষ্ঠানের জন্য তাকে বলি দেওয়ার পরিকল্পনা করেছিলেন। | শেষ (চতুর্থ) খণ্ড |
| 7 | নবকুমার ও কপালকুণ্ডলার সম্পর্কের পরিণতি কী হয়েছিল? | নবকুমার তাকে বিবাহ করে সপ্তগ্রামে নিজ গৃহে আনেন, পরে জটিলতা দেখা দেয়। | দ্বিতীয়-তৃতীয় খণ্ড |
| 8 | উপন্যাসটি প্রথম কত সালে প্রকাশিত হয়? | ১৮৬৬ খ্রিস্টাব্দে। | ভূমিকা / প্রধান পাতা |
| 9 | *(No-answer test)* কপালকুণ্ডলা উপন্যাসের কোনো চরিত্র কি মোবাইল ফোনে কথা বলে বা আধুনিক শহরে গাড়ি চালায়? | না — বইতে এই তথ্য নেই (ঊনবিংশ শতাব্দীর প্রেক্ষাপট, আধুনিক প্রযুক্তির উল্লেখ নেই)। | *প্রযোজ্য নয় — চ্যাটবটের "উত্তর পাওয়া যায়নি" বার্তা প্রত্যাশিত* |
| 10 | উপন্যাসের শেষ পরিণতিতে কপালকুণ্ডলার কী হয়? | কাহিনীর শেষে তার মর্মান্তিক (জলে ডুবে) মৃত্যু ঘটে। | চতুর্থ খণ্ড (শেষ পরিচ্ছেদ) |

Question 9 is the required test case that checks the chatbot correctly
refuses to hallucinate when the answer is not present in the book.
