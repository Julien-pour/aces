from typing import Optional, Union, List
import json

import numpy as np
import textwrap
import copy

from pydantic import BaseModel,Field
# from openelm.utils.code_eval import find_first_argument_of_first_function
# from openelm.environments.p3.prompt_code import base_persona_code, prompt_gen_description
# from openelm.environments.p3.prompt_code import prompt_rd_gen,prompt_elm,prompt_aces,prompt_aces_elm,instruction_solve_puzzle,list_subskills,prompt_wizard_coder
# from openelm.utils.code_eval import extract_arguments_except_first_specific
skill_list = [
    "String Manipulation",
    "Mathematical Operations",
    "Conditional Logic",
    "Recursion",
    "Brute Force Search",
    "Dynamic Programming",
    "Greedy Algorithms",
    "Backtracking",
    "Set Operations",
    "Permutations and Combinations",
    "Probability and Statistics",
    "Pattern Recognition", 
    "Sorting and Ordering",
    "Binary Operations (bitwise shifting, AND, OR)",
    "Geometry and Coordinate Manipulation",
    "Algorithm Optimization",
    "Number Theory (factors, primes, etc.)",
    "Graph Theory (paths, edges, vertices)",
    "Array Indexing",
    "Hashing"
]
# add Set Operations and Hashing




# class for instructor skill labelling prompt for P3
def get_class_PuzzleCheck(mode):
    match mode:
        case "description":
            class PuzzleCheck(BaseModel):
                """Puzzle description and if it should be given to the student or not."""
                puzzle_description: str = Field(description="Provide a brief, one to two sentence summary of the puzzle's content.")

        case "description+is_valid":
            class PuzzleCheck(BaseModel):
                """Puzzle description and if it should be given to the student or not."""
                puzzle_description: str = Field(description="Provide a brief, one to two sentence summary of the puzzle's content.")
                explanations: str = Field(decription="Short explanation of whether the puzzle should be given to the student or not.")
                give_puzzle_to_student: bool = Field(description="Whether the puzzle should be given to student or not based on the previous explanations")
    return PuzzleCheck

class Topics_evaluation(BaseModel):
    """List of topics that are used in the problem and solution."""
    explanations_index_topics: str = Field(decription="Short explanation of the specific topics employed in the puzzle.")
    index_topics: List[int] = Field(description="list of at most 5 index correponding to topics that are actually used in the problem `f` or the solution `g`")






def create_prompt_label(puzzle : str, mode="give_skills"):
    """
    create prompt for label_puzzle goes with Topics_evaluation class with give_skills=True
    mode = "give_skills", "is_valid", "description", "description+is_valid", "general"
    is_valid -> filtering 
    description use to give a description of the puzzle
    """

    # level = "master's student in CS"#"master's student"
    # skills format
    format_skills=""
    for idx,skill in enumerate(skill_list):
        format_skills+=f"{idx}. {skill}\n"
    skills = f"\n{format_skills}"
    
    base_persona = base_persona_code#.format(level=level)
    match mode:
        case "is_valid": # WIP should also use a persona to label the puzzle
            prompt=base_persona
            prompt += "Your role is to check if the following puzzle could be used or not."
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"
        case "description": # WIP 
            arg=find_first_argument_of_first_function(puzzle)
            puzzle=puzzle.split('def g')[0].strip() + "\n\ndef g(...):\n\nassert f(g()) == True"
            prompt=prompt_gen_description.format(arg_sol=arg,arg_solb=arg,puzzle=puzzle)
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"
        case "description+is_valid": # WIP
            arg=find_first_argument_of_first_function(puzzle)
            puzzle=puzzle.split('def g')[0].strip() + "\n\ndef g(...):\n\nassert f(g()) == True"
            prompt=prompt_gen_description.format(arg_sol=arg,arg_solb=arg,puzzle=puzzle)
            prompt += f"\nThen you should check if the following puzzle could be used or not to teach Python to {level}."
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"
        case "give_skills":
            prompt = base_persona+"\n"
            prompt+= "The Professor want to evaluate the diversity of those puzzles, can you label the following puzzle given the following list of topics, please?"
            # prompt = "Your role is: given the following puzzle, and the list of topics, exctract the information requested."
            prompt += "\nThe list of topics is:\n"+ skills 
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"
        case "give_skills_no_instructor": # WIP 
            prompt = base_persona+"\n"
            prompt+= "The Professor want to evaluate the diversity of those puzzles, can you label the following puzzle given the following list of topics, please?"
            # prompt = "Your role is: given the following puzzle, and the list of topics, exctract the information requested."
            prompt += "\nThe list of topics is:\n"+ skills 
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"            
            prompt += "Respond with two or three sentence explaning the topics used in the puzzle.\n"
            prompt += "Then summarize your response by giving a list from 1 to 5 index corresponding to topics that are actually used in the puzzle above in this format: 'The list of skill use is: [].' where [] is the list of index of the topics used in the puzzle for example [3,5,6]."

        case "general":
            prompt= "Given the following puzzle, exctract the information requested."
            prompt += "\n\nThe puzzle is:\n```python\n" + puzzle + "\n```\n"
            
    return prompt


def get_programming_puzzles_prompt(
        list_few_shot_example : List[str],
        skill_targeted: Optional[List[int]]=None,
        n_fewshot_ex=3,
        aces_elm_mode=False,
    ):
    """
    should change that to list_few_shot_example from list to Phenotype type
    skill_targeted list of binary vector [(0/1)]^n_skills indicating if the skill is targeted or not
    remove n_fewshot_ex
    """
    extra_prompt=""
    prompt = copy.deepcopy(prompt_aces)
    if aces_elm_mode:
        prompt = copy.deepcopy(prompt_aces_elm)

    # if wizard_coder:
    #     prompt = copy.deepcopy(prompt_wizard_coder)
    #     few_shot_example_gen_puzzle="base"
    #     extra_prompt += evolve_instructions()
    if not isinstance(list_few_shot_example, list):
        list_few_shot_example = [list_few_shot_example]
    if all(isinstance(x, str) for x in list_few_shot_example):
        raise NameError("should be phenotype not str") 

    puzzles = [puzz for puzz in list_few_shot_example[:n_fewshot_ex]]
    
    examples = ""
    for i, puzzle in enumerate(puzzles):
        puzzle_description = puzzle.description 
        prompt_cot_fitness = ""
        skill_puzzle_i=""
        prompt_cot_fitness = f"\n\n- Difficulty score: {int((puzzle.fitness+1)*100)} out of 100"

        skill_puzzle_i="\n\n- This puzzle has the following skills:"
        idx_skill_targeted = [idx for idx, val in enumerate(puzzle.emb) if val]
        for idx in idx_skill_targeted:
            skill_puzzle_i += f"\n* {skill_list[idx]}"

        examples += f"\nPuzzle {i}:\nPuzzle description: {puzzle_description}{prompt_cot_fitness}{skill_puzzle_i}\n\n```python\n{puzzle.program_str}\n```\n"    

    skill_target=":"
    idx_skill_targeted = [idx for idx, val in enumerate(skill_targeted) if val]
    for idx in idx_skill_targeted:
        skill_target += f"\n- {skill_list[idx]}"

    extra_prompt += "You should aim to generate puzzles with a Difficulty score between 90 and 100 out of 100."
    prompt = prompt.format(examples=examples,skill_target=skill_target,extra=extra_prompt)
    # prompt += prompt2add
    return prompt


def evolve_instructions() -> None:
    """wizard coder instruction from https://github.com/nickrosh/evol-teacher/blob/main/generate_evol.py"""
    methods = [
    'Add new constraints and requirements to the original problem, adding approximately 10 additional words.',
    'Replace a commonly used requirement in the programming task with a less common and more specific one.',
    'If the original problem can be solved with only a few logical steps, please add more reasoning steps.',
    'Provide a piece of erroneous code as a reference to increase misdirection.',
    'Propose higher time or space complexity requirements, but please refrain from doing so frequently.'
    ]
    chosen_method = np.random.choice(methods)
    prompt_extra = f"Generate 5 Python Programming Puzzles by increasing the difficulty of the given programming puzzles a bit.\n\nYou can increase the difficulty using, but not limited to, the following methods:\n{chosen_method}"
    return prompt_extra


def prompt_solve_puzzle_given_f(problem_str: str): 
    """
    prompt to solve a puzzle (generate g) given f
    """
    try:
        arg_sol = extract_arguments_except_first_specific(problem_str)
    except:
        arg_sol= "..."
    # arg_sol= "..."#get_inputs(problem)
    f = problem_str.split("def g")[0].strip()
    full_prompt=instruction_solve_puzzle.format(f=f,arg_g=arg_sol)
    

    return full_prompt



base_persona_code ="""You are a helpful assistant to a Professor teaching a programming course in Python. 
The Professor want to give Pyhton programming puzzles to his Computer Science student to teach them Python.
A Python programming puzzle is defined by two functions, the puzzle f(…) and the solution g(…). f defines an algorithmic challenge, and g solves this challenge. g is a solution to f if and only if f(g()) == True."""

prompt_gen_description="""A Python programming puzzle is defined by two functions, the problem f(solution, arg1=value1, arg2=value2, ..) and the solution. f defines an algorithmic puzzle, and the solution solves this puzzle.
You should pay a particular attention that the puzzle is solved if and only if **f(solution) == True**.
Your role is to write a one or two sentence the description of the puzzle's goal (what the solution should be), remember that the solution that satisfy the goal must be given as the first argument of `f`.
You can start by: 'Find the solution: {arg_sol} (describe its type shortly) that should (here you should speak about the solution: {arg_solb} and how it should solve all the constraints of the puzzle with respect to others args (describe their types shortly)) ...'. 
For example:
'Given a string `str1`, find the length of the longest substring without repeating characters.'
'Given two sorted arrays `nums1` and `nums2` of size `m` and `n` respectively, return the median of the two sorted arrays.'


The puzzle is:
```python
{puzzle}
```
"""


prompt_aces= """Consider Python Programming Puzzles (P3). P3 consists of two functions: a problem function `f` and its corresponding solution `g`. The challenge lies in constructing a SAT problem `f` and a function `g` such that `f(g())` evaluates to `True`

## Main Rules:
- Each puzzle includes two functions: `def f(...)` and `def g(...)`.
- The first argument of `f` is always the output from `g()`.
- Ensure `f` and `g` have matching argument signatures (e.g., `def f(solution, arg1=value1, arg2=value2, ...)` and `def g(arg1=value1, arg2=value2, ...)`). You also need to set the value of argument of f (arg1,arg2,...) and g when you define them.
- Avoid using `f` inside `g`, and `g` inside `f`.
- Include any necessary imports so your code runs smoothly.
- Give a clear Puzzle description that must be brief and diverse compared to the other puzzles.
- Make sure the puzzle is self-contained within these two functions.
- Make sure that that each puzzle have just all required skills (see below)

## P3 Format:
Puzzle description: A two to four sentence summary of the puzzle's content. To explain what is the problem `f`, and how you can solve it with `g`. 
```python
def f(solution, args=...) -> bool:
    # Python code to test the solution returned by g.
    # This function is a test unit and must return True if the solution is correct, and False otherwise.

def g(args=...) -> solution:
    # Python code to generate a solution for the problem.
    # The solution should generalize to all possible args.
    return solution

assert f(g()) == True
```

## Examples:
{examples}

Generate 5 P3 similar to previous Examples. Ensure that all new puzzles are more challenging than Puzzle from previous examples.
{extra}

**Please make sure that new puzzles have JUST ALL the following skills**{skill_target}
## New 5 problems:
"""


prompt_aces_elm= """Consider Python Programming Puzzles (P3). P3 consists of two functions: a problem function `f` and its corresponding solution `g`. The challenge lies in constructing a SAT problem `f` and a function `g` such that `f(g())` evaluates to `True`

## Main Rules:
- Each puzzle includes two functions: `def f(...)` and `def g(...)`.
- The first argument of `f` is always the output from `g()`.
- Ensure `f` and `g` have matching argument signatures (e.g., `def f(solution, arg1=value1, arg2=value2, ...)` and `def g(arg1=value1, arg2=value2, ...)`). You also need to set the value of argument of f (arg1,arg2,...) and g when you define them.
- Avoid using `f` inside `g`, and `g` inside `f`.
- Include any necessary imports so your code runs smoothly.
- Give a clear Puzzle description that must be brief and diverse compared to the other puzzles.
- Make sure the puzzle is self-contained within these two functions.

## P3 Format:
Puzzle description: A two to four sentence summary of the puzzle's content. To explain what is the problem `f`, and how you can solve it with `g`. 
```python
def f(solution, args=...) -> bool:
    # Python code to test the solution returned by g.
    # This function is a test unit and must return True if the solution is correct, and False otherwise.

def g(args=...) -> solution:
    # Python code to generate a solution for the problem.
    # The solution should generalize to all possible args.
    return solution

assert f(g()) == True
```

## Examples:
{examples}

Generate 5 P3 similar to the last Examples (Puzzle 2). Ensure that all new puzzles are more challenging than Puzzle 2.
{extra}

**Please make sure that new puzzles have JUST ALL the following skills**{skill_target}
## New 5 problems inspired by Puzzle 2:
"""

instruction_solve_puzzle = '''You will be given a function. Respond only in code with a correct, efficient implementation of the function. You will need to generate the correct solutions (g), for the Problem 2 that satisfies the condition f(g()) == True.

Problem 0:
```python
def f(stamps: List[int], target=80, max_stamps=4, options=[10, 32, 8]) -> bool:
    """Find a selection of at most max_stamps stamps whose total worth is the target value."""
    for s in stamps:
        assert s in options
    return len(stamps) <= max_stamps and sum(stamps) == target
```
Solution 0:
```python
def g(target = 80, max_stamps = 4, options = [10, 32, 8]):
    from itertools import combinations_with_replacement
    for n in range(max_stamps + 1):
        for c in combinations_with_replacement(options, n):
            if sum(c) == target:
                return list(c)

assert f(g()) == True
```

Problem 1:
```python
from typing import*
def f(ans: List[List[int]], target=2) -> bool:
    """
    Find a list of pairs of integers where the number of pairs in which the second number is more than
    two greater than the first number is a given constant
    """
    for i in range(len(ans)):
        a, b = ans[i]
        if b - a >= 2:
            target -= 1
    return target == 0
```

Solution 1:
```python
def g(target = 2):
    return [[0, 2]] * target 

assert f(g()) == True
```

Now you need to give the solution (def g({arg_g}):) to the following Problem 2 that satisfies the condition f(g()) == True.

Problem 2:
```python
{f}
```
'''


prompt_wizard_coder = """Consider Python Programming Puzzles (P3). P3 consists of two functions: a problem function `f` and its corresponding solution `g`. The challenge lies in constructing a SAT problem `f` and a function `g` such that `f(g())` evaluates to `True`

## Main Rules:
- Each puzzle includes two functions: `def f(...)` and `def g(...)`.
- The first argument of `f` is always the output from `g()`.
- Ensure `f` and `g` have matching argument signatures (e.g., `def f(arg0, arg1=value1, arg2=value2, ...)` and `def g(arg1=value1, arg2=value2, ...)`). You also need to set the value of argument of f (arg1,arg2,...) and g when you define them.
- Avoid using `f` inside `g`, and `g` inside `f`.
- Include any necessary imports so your code runs smoothly.
- Give a clear Puzzle description that must be brief and diverse compared to the other puzzles.
- Make sure the puzzle is self-contained within these two functions.

## P3 Format:
Puzzle description: A two to four sentence summary of the puzzle's content. To explain what is the problem `f`, and how you can solve it with `g`. 
```python
def f(solution, args=...) -> bool:
    # Python code to test the solution returned by g.
    # This function is a test unit and must return True if the solution is correct, and False otherwise.

def g(args=...) -> solution:
    # Python code to generate a solution for the problem.
    # The solution should generalize to all possible args.
    return solution

assert f(g()) == True
```

## Examples:
{examples}

Generate 5 different P3 similar to previous Examples.
{extra}

## New 5 problems:
"""
