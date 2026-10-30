# Recruiting the 20 test families

The test needs 20 families who finish at least one search, from at least three channels, each
recorded with `--channel` so the report can tell them apart. Use these channel names: `family`,
`friends`, `whatsapp-group`, `linkedin`, `x`, `other`.

Every invite sends people to [reclaim.doaide.com](https://reclaim.doaide.com). The page walks them
through the official portals and stores nothing on a server. When they finish, they tap "Send on
WhatsApp" and send the result to you. Ask for that message even when nothing turned up: a family
that searched and found nothing counts just as much as one that found something.

## When results arrive

1. Send [consent script v1](HIT_RATE_TEST.md#consent-script-v1) word for word and wait for an okay.
   Until then record nothing. If they say no, delete their message and record nothing.
2. `python3 -m reclaim new --consent --channel <channel>` prints the case id (R001). Keep the
   case-to-person mapping outside this tool.
3. Save their message to a file and run `python3 -m reclaim record R001 --reply reply.txt`. Their
   relatives and results come in together, all or nothing. If a line is refused, the error names it:
   ask them about that line rather than guess.
4. Ask roughly how long it took: `python3 -m reclaim done R001 --minutes <their answer>`.
5. If they found something, run `python3 -m reclaim card R001 --png` and send them `card.png`. A week
   later, ask whether they shared it: `python3 -m reclaim shared R001 yes|no`.
6. If a portal stopped them, ask what it asked for. The first family to search IEPF should note its
   exact fields, since they are not verified yet.

The page is in English. For relatives who prefer Hindi, send the Hindi invite and do the first search
together on a call.

## WhatsApp, one to one (family and friends)

> Hi! I'm testing a free guide that helps families check the government's official portals for
> money a relative may have left behind: old bank accounts, shares and dividends, LIC and other
> insurance, and mutual funds. RBI alone holds ₹86,917 crore of unclaimed deposits.
>
> It takes an evening: https://reclaim.doaide.com
> Add the relatives you want to check (start with anyone who has passed away), open each official
> site from the page and mark what you see. Type PAN, dates of birth and account numbers only on
> the official sites, never on the page and never to me.
>
> When you're done, tap "Send on WhatsApp" and send it to me, even if nothing turned up. That helps
> just as much. I'll ask your okay before noting anything down.

Hindi (pick रहा or रही, and लूँगा or लूँगी, before sending):

> नमस्ते! मैं एक मुफ़्त गाइड टेस्ट कर रहा/रही हूँ, जिससे परिवार सरकार के आधिकारिक पोर्टल पर देख
> सकते हैं कि किसी रिश्तेदार का पैसा कहीं छूट तो नहीं गया: पुराने बैंक खाते, शेयर और डिविडेंड, LIC
> और दूसरे बीमे, और म्यूचुअल फंड। सिर्फ़ RBI के पास ₹86,917 करोड़ की ऐसी जमा राशि है जिस पर किसी
> ने दावा नहीं किया।
>
> एक शाम का काम है: https://reclaim.doaide.com
> जिन रिश्तेदारों के लिए देखना है उन्हें जोड़ें (जो अब नहीं रहे, उनसे शुरू करें), पेज से हर आधिकारिक
> साइट खोलें और जो दिखे वह मार्क करें। PAN, जन्मतिथि और खाता नंबर सिर्फ़ आधिकारिक साइट पर डालें,
> इस पेज पर या मुझे कभी नहीं।
>
> हो जाने पर "Send on WhatsApp" दबाकर मुझे भेज दें, कुछ न मिले तब भी। वह भी उतना ही काम का है।
> कुछ भी नोट करने से पहले मैं आपकी अनुमति लूँगा/लूँगी।

## WhatsApp groups (society, alumni, office)

> Money from old bank accounts, shares, insurance and mutual funds often sits unclaimed with RBI,
> SEBI, IRDAI, IEPF and LIC, especially when the holder has passed away. I'm testing a free guide
> that walks a family through the official portals in one evening: https://reclaim.doaide.com
> (no sign-up, and it stores nothing). I'm looking for families who will try it this week and tell
> me what they found, or where they got stuck. Message me if you're in.

Hindi:

> पुराने बैंक खातों, शेयरों, बीमे और म्यूचुअल फंड का पैसा अक्सर RBI, SEBI, IRDAI, IEPF और LIC के पास
> बिना दावे के पड़ा रहता है, ख़ासकर जब खाताधारक नहीं रहे। मैं एक मुफ़्त गाइड टेस्ट कर रहा/रही हूँ जो
> एक शाम में आधिकारिक पोर्टल पर खोज करवाती है: https://reclaim.doaide.com (न साइन-अप, न कोई डेटा
> सेव होता है)। इस हफ़्ते जो परिवार इसे आज़माकर बता सकें कि क्या मिला या कहाँ अटके, मुझे मैसेज करें।

## LinkedIn

> ₹86,917 crore sits unclaimed in Indian bank accounts (RBI, June 2026). Add an estimated ₹1.84
> lakh crore in unclaimed shares and dividends, and over ₹12,700 crore in insurance and mutual
> funds. Some of it may be your family's.
>
> The government has built portals to search it: RBI's UDGAM, IEPF, LIC's list, IRDAI's Bima
> Bharosa and SEBI's MITRA. Each one asks for different details, so it is hard to know where to
> start.
>
> I built a free guide that turns it into one evening. List your relatives, see which searches you
> can run with the details you have, open each official portal and mark what you find. It never
> asks for PAN or Aadhaar and stores nothing on a server.
>
> I'm looking for 20 families to try it this week and tell me what they found, or where they got
> stuck. Comment or DM me.
>
> https://reclaim.doaide.com
> Open source: https://github.com/DoAideAi/DoAide-Reclaim

## X

> ₹86,917 crore sits unclaimed in Indian bank accounts (RBI, June 2026), and more in old shares,
> insurance and mutual funds.
>
> Free guide to check every relative on the official portals in one evening:
> https://reclaim.doaide.com
>
> Looking for 20 families to try it this week. DM me.

## Dhanteras push (until Friday 6 November)

Dhanteras is the day families buy gold, so the push asks them to look for the family's forgotten
money first. Send people to [reclaim.doaide.com/dhanteras](https://reclaim.doaide.com/dhanteras/):
it is in Hindi and English, gives the three steps and links to the guide. In family groups send the
card image first (the page's download button, or https://reclaim.doaide.com/dhanteras/card.png) and
the message right after it. A link sent on its own unfolds into a large preview image.

Results arrive exactly as above: the guide's "Send on WhatsApp" lines, consent script first, the same
channel names. The case dates show which families came in during the push.

## Dhanteras: WhatsApp family group

Hindi (pick रहा or रही before sending):

> इस धनतेरस सोना ख़रीदने से पहले एक काम कर लीजिए: देख लीजिए कि परिवार का कोई पैसा सरकार के पास
> बिना दावे के तो नहीं पड़ा। दादा-दादी, नाना-नानी या माता-पिता के पुराने बैंक खाते, शेयर, LIC और
> म्यूचुअल फंड। सिर्फ़ RBI के पास ₹86,917 करोड़ ऐसे पड़े हैं।
>
> सरकारी साइटों पर एक शाम में खोजने का मुफ़्त तरीका: https://reclaim.doaide.com/dhanteras/
> PAN और जन्मतिथि सिर्फ़ सरकारी साइट पर डालें, कहीं और नहीं।
>
> कुछ मिले तो मुझे बताइए, कुछ न मिले तब भी। मैं 20 परिवारों के साथ इसे टेस्ट कर रहा/रही हूँ।

English:

> Before buying gold this Dhanteras, check whether any of the family's money is sitting unclaimed
> with the government: grandparents' or parents' old bank accounts, shares, LIC and mutual funds.
> RBI alone holds ₹86,917 crore of it.
>
> A free way to search the official sites in one evening: https://reclaim.doaide.com/dhanteras/
> Type PAN and dates of birth only on the official sites, nowhere else.
>
> Tell me what you find, even if it's nothing. I'm testing this with 20 families.

## Dhanteras: X

> Before buying gold this Dhanteras, check the government's unclaimed-money portals for your
> family: old bank accounts, shares, LIC, mutual funds. RBI alone holds ₹86,917 crore.
>
> Free guide, one evening, in Hindi and English:
> https://reclaim.doaide.com/dhanteras/

## Pace

Twenty finished families in two weeks probably takes 40 to 60 invites. That is a guess, not a
measured rate: after the first ten invites, count the replies and adjust.
