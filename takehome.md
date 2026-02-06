# Take-Home Project: AI-Powered Alcohol Label Verification App

## Project Background & Stakeholder Context

*The following document contains notes from our discovery sessions with the Compliance Division, along with technical requirements for the prototype. Pay close attention to the stakeholder interviews—they contain important context about the users, their workflows, pain points, and the environment your solution needs to work within.*

### Interview Notes: Sarah Chen, Deputy Director of Label Compliance

*Conducted Tuesday, 3:15 PM — Sarah was running late from her daughter's school play rehearsal*

"Thanks for meeting with me. Sorry about the delay—my daughter's playing the lead in her school's production of *Annie* next week and rehearsals have been crazy. Anyway, let me tell you about what we're dealing with here.

So the TTB reviews about 150,000 label applications a year. Our team of 47 agents handles all of them. Each application includes images of proposed labels—front, back, sometimes neck labels or case boxes. An agent might review 40-60 labels in a day, depending on complexity. The simple ones—your standard domestic beer labels—those can be quick, maybe 3-4 minutes. But imported spirits with foreign language elements, health claims, or organic designations? Those can take 20-30 minutes of cross-referencing regulations.

The actual review process is pretty straightforward. An agent pulls up an application, looks at the label images, and checks them against our regulations. Is the mandatory information present? Is the alcohol content displayed correctly? Is the government warning statement there and properly formatted? Are there any prohibited claims or misleading statements? Then they either approve, reject with specific citations, or send it back for corrections.

Here's the thing though—and this is what got leadership interested in AI—a lot of what we do is just... checking that stuff is there. Like, does this label have the government warning? Is the alcohol content displayed? Those are objective, checkable things. If an AI tool could handle those first-pass checks, our agents could focus on the subjective stuff—evaluating marketing claims, checking for misleading imagery, that kind of thing.

Oh, I should mention—we tried a pilot with the scanning vendor last year. Disaster. The system would take 45 seconds to process a single label, and by that time, an experienced agent could have already finished their review. **If we can't get results back in about 5 seconds, nobody's going to use it.** We learned that the hard way.

What else... The agents really vary in their tech comfort level. Dave's been here since the Clinton administration and still prints his emails. Jenny started last year and keeps asking why we don't have a mobile app. Whatever you build needs to be something **my mother could figure out**—she's 73 and just learned to video call her grandkids last year, if that gives you a benchmark. Half our agents are north of 50, and the last system rollout had a six-month adoption period because the interface was too complicated.

One more thing that came up in our last team meeting—during peak season, we get these big importers submitting 50+ labels at once. Right now, agents have to check each one individually. If the new tool could **handle batch uploads**, that would be huge. Janet from our Seattle office has been asking about this for years."

### Interview Notes: Marcus Williams, IT Systems Administrator

*Coffee chat, Thursday morning*

"Sarah probably gave you the business side. Let me fill you in on some of the technical landscape.

Our current infrastructure is... well, it's government infrastructure, let's leave it at that. We're on AWS GovCloud for some things, but a lot of our systems are still on-prem. The label review system—COLA Online—is a legacy web application that's been around since 2007 with various patches and updates.

The COLA system is built on .NET, though there's been talk about modernizing it for years. We had a containerization initiative that got about 60% done before the contractor's budget ran out. Fun times.

For this prototype, we're not looking to integrate with COLA directly—that's a whole different beast with its own security review process. What we need is a standalone tool that agents can use alongside COLA. Think of it as a 'second screen' tool—they pull up the label in COLA, then use your tool to do a quick automated check.

Security-wise, we'd need to be careful with any production deployment—there's PII considerations, data classification concerns, the whole FedRAMP thing. But for the prototype, don't worry about all that. Just build something that works and we can worry about the compliance stuff later.

Oh, and our network blocks outbound traffic to a lot of domains, so keep that in mind if you're thinking about external API calls. For a prototype, it's fine—we can test it outside the network—but it's something we'd need to address for production."

### Interview Notes: Dave Morrison, Senior Compliance Agent (28 years)

*Brief hallway conversation*

"Look, I'll be honest, I've seen a lot of these 'modernization' projects come and go. Remember the automated scanning thing last year? Spent six months training us on it, then it couldn't even tell the difference between a wine label and a spirits label half the time. I went back to doing it manually within a week.

The thing about label review is there's nuance. You can't just pattern match everything. Like, I had a case last month where a bourbon label said 'Made with Kentucky limestone water'—technically that's a geographic reference that needs substantiation, but it's also a common industry practice that we've historically allowed. A computer's going to flag that every time.

That said, I'm not against new tools. If something can help me get through my queue faster, great. Just don't tell me it's going to replace my judgment. And please, make it simple. I don't need seventeen tabs and a dashboard. Give me a button that says 'check this label' and tell me what it found."

### Interview Notes: Jenny Park, Junior Compliance Agent (8 months)

*Teams call, Friday afternoon*

"I'm so excited you're working on this! When I started here, I was kind of shocked at how manual everything is. I mean, I'm literally squinting at label images trying to read tiny text to verify the warning statement is word-for-word correct. My eyes are killing me by end of day.

The one thing I'd say is the warning statement check is actually trickier than it sounds. It has to be **exact**. Like, word-for-word, and the 'GOVERNMENT WARNING:' part has to be in all caps and bold. Sarah probably told you about the basic requirements, but there are edge cases—sometimes it's split across two panels, sometimes the font is barely legible. And don't even get me started on labels with artistic backgrounds that make the text hard to read.

Also—and this is maybe out of scope for a prototype—but it would be amazing if the tool could handle labels that aren't in English. We get a ton of imports, and checking foreign language labels against our requirements is a whole different challenge. Even just flagging 'hey, this might not be in English' would save time."

## Technical Requirements

You are free to use any programming languages, frameworks, or libraries you prefer. We want to see what you'd reach for and how you'd approach it. There are no technology restrictions—choose the tools that you think best fit the problem. Cloud APIs, open source models, custom solutions—whatever you think makes sense. We're looking for thoughtful technical decisions, not any specific stack.

## Additional Context

### About TTB Label Requirements

For reference, TTB requires specific information on alcohol beverage labels. The exact requirements vary by beverage type (beer, wine, distilled spirits), but common mandatory elements include:

- Brand name
- Class/type designation
- Alcohol content (with some exceptions for certain wine/beer)
- Net contents
- Name and address of bottler/producer
- Country of origin for imports
- **Government Health Warning Statement** (mandatory on all alcohol beverages)

We encourage you to review TTB's guidelines at ttb.gov for additional context on label requirements.

### Sample Label

Your app should handle labels containing information like the example below:

**Example Distilled Spirits Label Fields:**

- Brand Name: "OLD TOM DISTILLERY"
- Class/Type: "Kentucky Straight Bourbon Whiskey"
- Alcohol Content: "45% Alc./Vol. (90 Proof)"
- Net Contents: "750 mL"
- Government Warning: [Standard government warning text]

*We encourage you to create or source additional test labels—AI image generation tools work well for creating realistic test images.*

## Deliverables

1. **Source Code Repository** (GitHub or similar)
   - All source code
   - README with setup and run instructions
   - Brief documentation of approach, tools used, assumptions made
2. **Deployed Application URL**
   - Working prototype we can access and test

## Evaluation Criteria

- Correctness and completeness of core requirements
- Code quality and organization
- Appropriate technical choices for the scope
- User experience and error handling
- Attention to requirements
- Creative problem-solving

We understand this is time-constrained. A working core application with clean code is preferred over an over-engineered solution that tries to do everything.

*Questions? Reach out for clarification—though we also value how you fill in gaps independently.*

Good luck!
