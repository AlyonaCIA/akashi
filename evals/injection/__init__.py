"""Prompt-injection evaluation for pull-request reviewers.

Cases are data: a pull request, an injected payload, and an attack objective. A reviewer
under test sees each case twice, with and without the payload; an attack succeeds only
if the payload changes the outcome in the attacker's favour.
"""
