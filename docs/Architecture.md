# Architecture Overview

## Goal
Simulate a League of Legends combat accurately enough to compare builds under explicit assumption.
This is a Simulator + Optimizer, not a stat scraper

## Non-Goals
1. Perfect 1:1 reproduction of LoL engine
2. Using winrates or popularity as the truth
3. Parsing UI text and using it as logic

## Core Principles
1. Damage is computed in one code only
2. Items are modifiers
