# Classifier for Congressional Bills

Final project for ECE 6130, Grid and Cloud Computing

Coded by [Brandon Bernier](mailto:bbernier@gwu.edu) 

This project attempts to predict how a given Congressman or Senator will vote on future legislation by analyzing their voting history on previous legislation. It makes use of the [Sunlight Congress API](https://sunlightlabs.github.io/congress/) to amass the entire recorded voting history for all legislators in Congress as well as the full text of all legislation that has been voted on. The classification algorithm works by creating two mutually exclusive lists of words from bills they have previously voted Yea and Nay on and attempts to compare the wording of new bills to those lists. With that comparison in hand as well as the political party of the sponsor of the bill, a fairly accurate prediction can be made.

## Usage

This project is tested using Python 2.7 due to necessary dependencies.

The python file includes all of the necessary functions for gathering and sorting through all of the data. At the bottom of the file, you can choose what specific functions you would like to run, what legislators histories to examine, etc. The project requires the full text of all bills, which can be downloaded from [United States Congress](https://github.com/unitedstates/congress) and the data scraper they provide.