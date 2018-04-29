setwd("~/Repos/SataliaNet")
#install.packages("dplyr")
library("dplyr", lib.loc="~/R/x86_64-pc-linux-gnu-library/3.2")
library("anytime", lib.loc="~/R/x86_64-pc-linux-gnu-library/3.2")

# import
standups_raw <- read.csv("StandUps.csv")
slackpriv_raw <- read.csv("SlackPrivate.csv")[2:9]
slackpub_raw <- read.csv("SlackPublic.csv")[2:15]

standups <- standups_raw[,c("user_id", "project_id", "interest_id", "time", "standup_date")]

#slackids <- data.frame(slackpub_raw[match(unique(slackpub_raw$userid),slackpub_raw$userid),c("userid", "username", "fullname")])
#slackids <- slackids[slackids$username != "",]
#standupids <- data.frame(standups_raw[match(unique(standups_raw$user_id),standups_raw$user_id),c("user_id", "name")])

# manual sync 
#write.csv(slackids, "slackids.csv")
#write.csv(standupids, "standupids.csv")
slackids <- read.csv("slackids.csv")[2:4]
standupids <- read.csv("standupids.csv")[2:3]
hubble_data <- read.csv("hubble_users.csv")

# ID join
ids <- right_join(slackids, standupids, by=c("fullname" = "name"))[,c(4,3,1,2)]
ids <- left_join(ids, hubble_data[,c(1,3)], by=c("user_id" = "id"))
colnames(ids) <- c("hubble_id", "name", "slack_id", "slack_user", "relationship")
ids <- ids[!is.na(ids$relationship) & !is.na(ids$slack_id),]
# check for non-joins
# anti_join(standupids, slackids, by=c("name" = "fullname"))
write.csv(ids, "id_list.csv")

# Standups conversion
standups_event <- left_join(ids, standups, by= c("hubble_id" = "user_id"))
# creating circles column
colnames(standups_event)[c(1,6,7,9)] <- c("id", "project", "interest", "date")
standups_event$name <- as.character(standups_event$name)
timelist <- strsplit(as.character(standups_event$time), ":")
standups_event$time <- as.numeric(lapply(timelist, '[[', 1))*60 + as.numeric(lapply(timelist, '[', 2))
standups_event$date <- as.Date(standups_event$date)
# export
write.csv(standups_event, "data_hubble.csv")

# Slack conversion - Public
slackpub <- left_join(ids, slackpub_raw, by = c("slack_id" = "userid"))
slackpub$message <- as.character(slackpub$message)
slackpub$members <- as.character(slackpub$members)
# not using channel status messages
pat <- c("has joined the channel", "set the channel", "archived the channel", "has left the channel")
slackpub <- slackpub[!grepl(paste(pat, collapse = "|"), slackpub$message) & slackpub$members != '[]',c(1,2,9,10,12,15,5)]
slackpub <- slackpub[!is.na(slackpub$hubble_id),]
# channels also filtered: risk, timetably, etc. (where memberlist is all or unavailable)
slackpub$date <- anydate(slackpub$timestamp)
# export
write.csv(slackpub, "data_slack_pub.csv")

# Slack conversion - Private
slackpriv <- left_join(ids, slackpriv_raw, by = c("slack_id" = "user_id"))[!is.na(slackpriv_raw$timestamp),c(1,2,8,10,5)]
slackpriv <- slackpriv[!is.na(slackpriv$hubble_id),]
slackpriv$members <- as.character(slackpriv$members)
slackpriv$mentions <- as.character(slackpriv$mentions)
slackpriv$date <- anydate(slackpriv$timestamp)
# export
write.csv(slackpriv, "data_slack_priv.csv")

# Satisfaction
satisfaction <- read.csv("satisfaction.csv")
colnames(satisfaction)[1:3] <- c('timestamp', 'name', 'id')
satisfaction[, c(4:23)] <- lapply(satisfaction[, c(4:23)], as.character)
l = c("Very Dissatisfied", "Dissatisfied", "Neither / NA", "Satisfied", "Very Satisfied")
ord <- function(x){
  return(factor(x, ordered = TRUE, levels = l))
}
satisfaction[, c(4:23)] <- lapply(satisfaction[, c(4:23)], ord)
satisfaction[, c(4:23)] <- lapply(satisfaction[, c(4:23)], as.numeric)
satisfaction$sat_score <- rowSums(satisfaction[, c(4:23)])

meta_full <- left_join(ids, satisfaction[, c(3,24)], by = c("hubble_id" = "id"))
meta_sat <- meta_full[!is.na(meta_full$sat_score), ]
meta_sat <- meta_sat[!duplicated(meta_sat[,c(1:2)]),]
