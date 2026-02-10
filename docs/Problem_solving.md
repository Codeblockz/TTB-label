started at 12:00pm 2/6/2026
First I downloaded the instructions, then I made a repository to View them in I broke everything down into markdown. I read the instructions over carefully. I then used Claude code to analyze the markdown and make a PRD. The plan is to use the PRD to make an app. I'll use claude code as an assistant to help with planning and structure. 

I'm going to utilize clog code to analyze the markdown file that was just made and help me plan a method for a MVP and choose a tech stack to use. 

I made a PRD with claude code. I will then utilize the task management tool and task manager to have it simultaneously make the code. I front-loaded my Claude MD file to have the set instructions so that I can reference where to go if it needs to reference, and my preferred coding standards and paradigms. 

I set up the Azure Foundry using the GPT-4o mini model and the Azure Vision Service on the regular Azure cloud system. 
The backend has been made, but it needs verification and validation, so phase one is complete, but No, validation has been done yet. 

Anthropic just rolled out a new feature. It's experimental. However, I want to see how well it can do. The time is 2:54. I am going to ask it to finish the rest of the project based on the PRD I'm going to have it create a team of agents each with their own specialty and division and testing. 

It came up with a plan is now 3:05 I Asked it to look at the remaining phases use the new teams tool and Work it out now that the plan has finished. Let's see how long it takes. 

It is now 3:44 and to my horror it appears to be complete. 

Started again at 4:48pm I am using claude code to test all features of the app.

Started again Feb 7
The app does not batch upload. It also does not match. It does not have a way to match, my wording was incorrect when I fed it to the LLM. I will now correct that. 

As Claude is working, it is important to keep track of what it's writing and approve. For example, it wrote that the application should be optional. I disagree. For the purpose of this app, it should be mandatory. The whole purpose is to make the process of matching the applications easier. Now in practice the applications to be matched should be from a database that we have somewhere But for this purpose they will fill out a form in case it is not readily available. 

I added AI generated labels for testing. I used chatGPT to create them. 
I asked claude code to create a UX testing team to check for functionality. I used plan -> then implement

The application did not show the matching to the form. 
Fixed that. Moving on the use of mock api interferring with speed test.
Out of fustration, I had the bot remove all mock points. I will pay for that later.

Had to change the buissness logic of checking labels. The llm was doing checks first with regex as redundency. I switched it for speed.

Feb 8. Thought about the government warning label, I messed up how the program searches for it. I will fix it now. I just reliezed I dont check for bold. I will need to add
that check.

Now its slow again, about 6 seconds. I feel like using the LLM just for bold is overkill, not to mention expensive. I will research alternatives.
Found openCV could be used for bold. I don't think it will work for this case because it needs non bold as a reference and there isnt a good way to anchor those.
However, I will test it anyways and see if it works.
Well, it works. However more testing is needed.

I will now set up the demo link.
Demo link works and have a script for easy set up.

Feb 9, Used the agents to create a stakeholder brief.
Brief made. It was Made for stakeholders and not a technical review. I think I could push this now to the web but just to be sure I want to make more data sets and test it a little more since I have until Friday. 
I added more test images and I made it so that in the front end you can select already made images. 

Feb 10
I want to circle back to the bold detection In the government warning. We use OpenCV because it's quick. However, it's not really accurate and that does not achieve The purpose of what we want we want to save time So we need to find a solution that doesn't take up more time that hits our five second window and is accurate. 
Now I need to fix the bold so it flags correctly.

I will use claude code to perform user testing. However, I expect the results to be poor because I do not know precisely what I need. The caveat of using an AI assistant is it only works well if you tell it what to do. If you tell it to think, it will fail. 

Claude Code made over 50 user test cases. As predicted it said everything is OK. 
I was feeling kinda iffy on the code base, so as precation I made it do a full scale code review. 