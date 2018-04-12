setwd("~/Repos/SataliaNet")
#install.packages("dplyr")
library("dplyr", lib.loc="~/R/x86_64-pc-linux-gnu-library/3.2")

# import
standups_raw <- read.csv("StandUps.csv")
slackpriv_raw <- read.csv("SlackPrivate.csv")[2:9]
slackpub_raw <- read.csv("SlackPublic.csv")[2:15]

standups <- standups_raw[standups_raw$draft == "False", c("user_id",  "standup_id", "project_name", "interest_id", "milestone_id", "calculated_time", "date")]
# i assume that people who stand up to the same project, meet once a week

#slackids <- data.frame(slackpub_raw[match(unique(slackpub_raw$userid),slackpub_raw$userid),c("userid", "username", "fullname")])
#slackids <- slackids[slackids$username != "",]
#standupids <- data.frame(standups_raw[match(unique(standups_raw$user_id),standups_raw$user_id),c("user_id", "name")])

# manual sync 
#write.csv(slackids, "slackids.csv")
#write.csv(standupids, "standupids.csv")
slackids <- read.csv("slackids.csv")[2:4]
standupids <- read.csv("standupids.csv")[2:3]

# ID join
ids <- right_join(slackids, standupids, by=c("fullname" = "name"))[,c(4,3,1,2)]
colnames(ids) <- c("hubble_id", "name", "slack_id", "slack_user")
# check for non-joins
anti_join(standupids, slackids, by=c("name" = "fullname"))
write.csv(ids, "id_list.csv")

# Standups conversion
standups_event <- left_join(standupids, standups)
# creating circles column
colnames(standups_event)[4] <- "project"
standups_event$name <- as.character(standups_event$name)
standups_event$project <- as.character(standups_event$project)
timelist <- strsplit(as.character(standups_event$calculated_time), ":")
standups_event$calculated_time <- as.numeric(lapply(timelist, '[[', 1))*60 + as.numeric(lapply(timelist, '[', 2))
standups_event$circle <- as.factor(sapply(strsplit(as.character(standups_event$project),"_"), '[', 1))
standups_event <- standups_event[!is.na(standups_event$standup_id),c(1,2,3,9,4,5,6,7,8)]
# export
write.csv(standups_event, "data_hubble.csv")

# Slack conversion - Public
slackpub <- left_join(ids, slackpub_raw, by = c("slack_id" = "userid"))
slackpub$message <- as.character(slackpub$message)
slackpub$members <- as.character(slackpub$members)
# not using channel status messages
pat <- c("has joined the channel", "set the channel", "archived the channel", "has ")
slackpub <- slackpub[!grepl(paste(pat, collapse = "|"), slackpub$message) & slackpub$members != '[]',c(1,2,9,10,12,5)]
# channels also filtered: risk, timetably, etc. (where memberlist is all or unavailable)
#
# export
write.csv(slackpub, "data_slack_pub.csv")

# Slack conversion - Private
slackpriv <- left_join(ids, slackpriv_raw, by = c("slack_id" = "user_id"))[,c(1,2,8,10,5)]
# export
write.csv(slackpriv, "data_slack_priv.csv")
