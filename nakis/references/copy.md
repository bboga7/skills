# Copy

Machine-made copy is rarely wrong. It is **interchangeable**: every sentence could appear on any
page, for any product, by anyone. Human copy is specific, a little uneven, and only fits one page.

This file has three parts: a method that applies to every language, a pattern list for English,
and a pattern list for Turkish. `scripts/audit.py` flags the most common patterns automatically.
The rest needs your judgment.

---

## 1. Method (all languages)

### The swap test

Read each sentence and ask: *could a competitor paste this onto their page without changing a word?*
If yes, rewrite it. This single test catches most problems.

| Interchangeable | Specific |
|---|---|
| We build innovative solutions for modern teams. | We build the scheduling tool for clinics that still use paper calendars. |
| Fast, reliable and secure. | Pages load in under a second on a 3G connection. |
| Passionate about design. | I redesigned the same checkout form eleven times until people stopped abandoning it. |

### Rules

1. **Concrete beats impressive.** A number, a name, a place, a date or a short story beats any adjective.
   If the user has not given you the detail, ask for it or leave a placeholder. Never invent it.
2. **Say what it does, not how it feels.** Replace "empowers you to" with the actual verb: sends, sorts, prints, books.
3. **One claim per section.** A section that promises three things is remembered for none.
4. **Write in the reader's words.** Use the terms the audience uses for their own problem, not industry jargon.
5. **Vary the rhythm.** Mix short and long sentences. Machine text tends to keep every sentence the same length.
6. **Cut the warm-up.** Delete the first sentence of a paragraph if the paragraph still works without it. It usually does.
7. **The button says what happens next.** "See the menu", "Book a 20-minute call", "Download the PDF (2 MB)".
   Not "Get started", "Learn more" or "Submit".
8. **Keep one voice.** Choose formal or informal, "we" or "I", and keep it for the whole page.
9. **Specific is not invented.** Being concrete means using the facts you were given well.
   It never means adding details about process, prices, outcomes or audiences that nobody gave you.
10. **Don't describe the website.** Lines about fonts, code or tracking are for designers, not for the reader.
    The same goes for interface behavior: say "Call us", not "tapping the number opens your phone app".
11. **Say it once.** Each fact appears once in the body. The main call to action appears at most twice,
    and one of those is at the end of the page. Contact details can repeat where the reader needs them.
    Repetition is what thin copy does to look full. A thin brief should make a short page.

### Structural patterns to avoid

These are not about words. They are about the shape of the text.

- **Everything in threes.** Three adjectives, three cards, three bullet points, again and again. Use two, four, or one.
- **Mirror sentences.** "It's not just X, it's Y." Once is a style. Twice is a pattern.
- **The question opener.** "Tired of X? Looking for Y?" Start with the answer instead.
- **Headline, one sentence, card grid.** The same rhythm repeated in every section.
- **Decorative emoji** as bullet points or in headings.
- **Dash overload.** Long dashes in every second sentence. Use a period or a comma.
- **Colon headlines.** "Speed: Built for performance." Rewrite as a plain sentence.
- **Title Case On Every Heading.** Sentence case reads more natural on most pages.
- **The empty finale.** Closing lines like "Let's build something amazing together." Close with a real next step.

---

## 2. English patterns

Flag these words and phrases. They are not forbidden, but each one should survive the swap test.

### Inflated verbs

elevate, unlock, unleash, empower, supercharge, revolutionize, transform, streamline, leverage, harness,
reimagine, redefine, delve, embark, foster, spearhead, skyrocket, amplify

### Empty adjectives

seamless, effortless, cutting-edge, next-level, world-class, best-in-class, state-of-the-art, robust,
innovative, game-changing, holistic, tailored, bespoke, curated, vibrant, dynamic, comprehensive, unparalleled

### Stock phrases

- in today's fast-paced world / in today's digital landscape
- whether you're a beginner or an expert
- look no further
- take your [x] to the next level
- say goodbye to [x]
- the future of [x]
- designed with you in mind / crafted with passion / built with love
- your journey / your one-stop shop / all in one place
- join thousands of [x]
- ready to get started? / ready to dive in?
- we're here to help / we've got you covered
- a testament to / plays a crucial role / navigate the complexities
- at the intersection of [x] and [y]

### Warm without new facts (English)

| Cold | Warm, nothing added |
|---|---|
| Our bakery has been operating since 1998. | Since 1998, this street's mornings have started in our oven. |
| Orders can be placed by phone. | We take orders by phone. One call is enough. |

### How to fix

| Pattern | Rewrite method | Example |
|---|---|---|
| "Elevate your workflow" | Name the task and the result | "Turn a 40-row spreadsheet into an invoice in one click" |
| "Seamless integration" | Say what connects to what, and how long it takes | "Connects to your calendar in two steps" |
| "Join thousands of users" | Use the real number, or remove it | "Used by 312 bakeries" or nothing |
| "Crafted with passion" | Show the evidence of care | "Every illustration on this page is drawn by hand" |

---

## 3. Turkish patterns

Turkish machine copy has an extra problem: it often reads like a **translation**. English sentence
structure, too many passive verbs and nouns made from verbs. Fix the sentence shape as well as the words.

### Hazır kalıplar (stock phrases)

- dijital dünyada / günümüzün hızla değişen dünyasında
- bir sonraki seviyeye taşıyın
- deneyimi yeniden tanımlıyoruz
- sınırları zorlayan / fark yaratan / alanında öncü
- yenilikçi çözümler / müşteri odaklı yaklaşım / uçtan uca çözümler
- sorunsuz bir deneyim / kesintisiz deneyim
- her şey tek bir platformda
- hayallerinizi gerçeğe dönüştürün
- potansiyelinizi ortaya çıkarın / gücünü keşfedin
- yolculuğunuz / yolculuğunuzda yanınızdayız
- sizin için özel olarak tasarlandı / tutkuyla tasarlandı
- binlerce mutlu müşteri
- hemen başlayın / hazır mısınız?
- bu bağlamda / bu doğrultuda / önemli bir rol oynar
- sadece X değil, aynı zamanda Y
- ister X olun ister Y

### Çeviri kokusu (translation smell)

| Belirti | Örnek | Düzeltme |
|---|---|---|
| Gereksiz edilgen yapı | "Raporlar sistem tarafından oluşturulur." | "Sistem raporları kendisi hazırlar." |
| "sağlamak / sunmak" ile isim fiil | "Hızlı destek sağlıyoruz." | "Sorunuzu aynı gün yanıtlıyoruz." |
| "-mektedir" yığını | "Ekibimiz çalışmaktadır." | "Ekibimiz çalışıyor." |
| Gereksiz "bir" | "Bir harika bir deneyim için" | "Rahat bir alışveriş için" |
| İngilizce söz dizimi | "Bizimle, işiniz büyür." | "İşinizi birlikte büyütelim." |
| "olarak" fazlası | "Ekip olarak, şirket olarak..." | Çoğu zaman silinebilir. |

### Uydurmadan sıcak yazmak (warm copy without new facts)

Sıcaklık yeni bilgiden değil, kuruluştan gelir: okura doğrudan seslenmek, kısa ve uzun cümleleri karıştırmak,
işin kendi kelimelerini kullanmak, bilinen bir bilgiyi bir sahne gibi anlatmak. Aşağıdaki örneklerin hiçbiri
brifte olmayan bir bilgi eklemiyor. Bunlar örnek; kalıp olarak kopyalama, kendi sayfanın sesini bul.

**Brif: mahalle fırını, 1998'den beri, sabah 6'da açılıyor, ekşi maya ekmek, sipariş telefonla.**

| Soğuk | Sıcak, yeni bilgi yok |
|---|---|
| Fırınımız 1998 yılından beri hizmet vermektedir. | 1998'den beri bu mahallenin sabahı bizim fırında başlıyor. |
| Çalışma saatlerimiz sabah 06.00'da başlamaktadır. | Kapımız sabah altıda açılıyor. |
| Ekşi maya ekmeklerimiz mevcuttur. | Ekmeğimiz ekşi mayayla. |
| Siparişleriniz için telefonla iletişime geçebilirsiniz. | Siparişi telefonla alıyoruz; bir arama yeter. |

**Brif: bisiklet tamircisi, 3 usta, aynı gün lastik tamiri, cumartesi kapalı, adres var.**

| Soğuk | Sıcak, yeni bilgi yok |
|---|---|
| Atölyemizde 3 usta görev yapmaktadır. | Tezgâhta üç usta var. |
| Lastik tamiri aynı gün içerisinde gerçekleştirilmektedir. | Patlak lastik aynı gün yola döner. |
| Cumartesi günleri kapalıyız. | Cumartesi biz de bisiklete biniyoruz; dükkân kapalı. |

Son örnek sınırda: "biz de bisiklete biniyoruz" brifte yok. Böyle bir cümle sayfaya değil, sahibine sunulan
öneri listesine gider. Sayfada kalacak hali: "Cumartesi kapalıyız."

Kontrol sorusu: **Bu cümle, brifteki bir bilgiyi daha insanca mı söylüyor, yoksa yeni bir bilgi mi ekliyor?**
İlki serbest, ikincisi öneri listesine.

### Turkish rules

1. **Etken çatıyı tercih et.** Kim ne yapıyor, açıkça söyle.
2. **Kısa cümle kur.** Türkçede yüklem sonda olduğu için uzun cümleler okuyanı yorar.
3. **"Siz" ya da "sen" seç ve değiştirme.** Sayfa boyunca aynı hitabı kullan.
4. **Somut fiil kullan.** "Çözüm sunuyoruz" yerine ne yaptığını söyle: kuruyoruz, onarıyoruz, teslim ediyoruz.
5. **Sahibi konuşuyormuş gibi yaz.** Sıcaklığı uydurma ayrıntıdan değil, sesten al: okura doğrudan seslen,
   zanaatın kendi kelimelerini kullan ("forma", "kasnak", "kapak geçirmek" gibi), aynı çağrıyı defalarca tekrarlama.
6. **Yazım kurallarına uy.** Bağlaç olan "de/da" ve soru eki "mi" ayrı yazılır. Kesme işareti yalnızca özel adlarda kullanılır.

---

## 4. Before you leave this step

- Every section passes the swap test.
- Every number, name and claim comes from the user, or is a visible placeholder.
- The headline was written after the body copy.
- Every button says what happens next.
