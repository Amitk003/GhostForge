# Overview

## What is GhostForge

GhostForge is a tool that watches network traffic and warns you before an attack completes.

Most security tools look at one network flow and decide if it is good or bad. GhostForge looks at the whole sequence. It learns what normal traffic looks like on your network, then spots when traffic starts to move toward an attack.

Think of it as a weather forecast for attacks. Instead of saying it is raining now, it says clouds are forming and rain is likely in 10 minutes.

## Why we built it

Security teams face three big problems:

1. Too many alerts. A typical team gets 1000 alerts per day. Almost half are false alarms. Analysts get tired and miss real threats.
2. Attacks are slow. A real attack has steps: scan, try to log in, move to another computer, set up control, steal data. One flow looks normal. The pattern is the clue.
3. Old data lies. Public datasets like CIC-IDS2018 have errors and hidden clues that do not exist in real networks. Models trained on them look good on paper but fail in real life.

GhostForge fixes this by learning normal behavior only from your own traffic, not from attack signatures. If an attack is new, it still looks like drift from normal.

## Who it is for

* SOC analysts who want fewer false alerts and clear reasons for each alert
* Enterprise networks that need early warning
* Critical infrastructure where normal traffic is stable and any drift matters

## What it does

* Ingests PCAP, CSV, or Zeek logs fully offline
* Builds a graph where hosts are nodes and flows are edges
* Learns normal graph changes with a world model
* Forecasts risk for the next 10 windows with a confidence range
* Maps forecast to MITRE ATT&CK stages
* Explains each forecast with top flows and technique links
* Lets you mark a forecast as correct or wrong so it learns

## What it does not do

* It does not block traffic by itself. It suggests what to check next, like which logs to pull. Blocking without human review can break business systems.
* It does not send your data to the cloud. Everything runs on your machine.
* It does not claim to be perfect. We report where we fail and how we test.

## Simple example

You upload a PCAP with a slow scan that you did not notice. GhostForge shows:

* Graph playback where one host suddenly talks to many ports on another host
* Risk line that goes from 0.1 to 0.7 over 5 windows
* Stage moves from Reconnaissance to Discovery
* Evidence table shows the 3 flows that caused the shift and links to MITRE T1595

You can then pull auth logs for the target host before the attacker moves further.
