# Overview

We're starting a new project from scratch. This project is intended to be a solution to simplify seedbox synchronisation for users of MyAnimeList and Sonarr.

The project should be a service which, on a schedule, awakens and, for each tracked user, queries MyAnimeList using its API for all anime for that user with the status "Plan to watch" or "Watching". For each such anime, the application should submit a request to Sonarr to search for that anime and track it.

Read the following information and build the project described, testing locally to ensure your work is functional where possible.

# Project structure

The project should be written in Python 3 using best-practice development methodologies and idiomatic syntax. 

The first iteration will only interact with Sonarr, but the application should be written in such a way that additional modules such as Radarr can be subsequently supported.

The system is intended to be containerised and distributed with Docker for deployment in locally-hosted clusters, so ensure that the project is structured to support this.

The directory contains the following files: a blank `README.md`, a `config.yaml` file with some prefilled config values, example MAL API requests/responses (`./mal_api_get_user_list`, `./mal_api_get_anime_details`), and `./tracked_users`, a plaintext file containing a list of users to track. Feel free to rearrange the files into more appropriate locations or use alternative configuration schemes based on your knowledge of Python project structure best-practices.

Ensure that configuration files are protected using an appropriately limited .gitignore file as this does not currently exist, remembering that other users are intended to pull the repo and supply their own configuration for users to track.

The project should contain appropriate logs with at least two levels, one for normal operation and one for debugging (verbose). 

The project should have an option to run manually and then terminate itself to enable point-in-time testing rather than the ordinary daemon mode. Embed this mode in whatever way is most appropriate based on the specified structure and deployment paradigm.

# Project functionality

As mentioned, the service is intended to run like a daemon, awakening every `SEARCH_FREQUENCY_MINUTES` and running the search function.

The search function should pull the anime lists one at a time for each user in `./tracked_users` (separated by new lines) using the appropriate endpoint from the MyAnimeList API, documented here: https://myanimelist.net/apiconfig/references/api/v2#operation/users_user_id_animelist_get

An example request/response is available in the file `mal_api_get_user_list`. You may assume that any user in `tracked_users` has a publically available list and thus setting up a session via OAuth is not required. The query parameter `status` can take one of 5 values: watching, completed, on_hold, dropped, plan_to_watch. We want to filter our call for the values `watching`, `plan_to_watch`, and `on_hold` (ie we do not want to retrieve `completed` or `dropped`).

After the list of appropriate anime for the user is collected, the API for Sonarr should be called to retrieve a list of tracked series. Configuration for the Sonarr server should be pulled from `config.yaml`.

After both of these lists are available, the service should compare the two lists for the diff; that is, create a new list which is all the titles in the response from calling MAL for each tracked user which is not in the list of tracked shows for Sonarr. Given that the titles may not be identical, make use of an appropriate matching strategy to give confidence that the entries are the same in MAL and Sonarr. You may make use of more explicit methods subsequently, eg tagging the entry in Sonarr as part of the request with the exact title when you queue it (or an appropriate equivalent).

Once we have the list of titles which are in the users' MAL lists but not Sonarr, the following process should execute:
1. For each title, call MAL's API for getting details for an anime, documented in `mal_api_get_anime_details` and here: https://myanimelist.net/apiconfig/references/api/v2#operation/anime_anime_id_get
2. If the anime does not have `"media_type": "tv"`, skip it and proceed to the next title
3. Make a request to Sonarr to monitor the show
4. (Optional) Apply some kind of indicator to the entry so that it can be matched exactly on future iterations of this process (such as the tagging method described above, but use judgement and make the best choice if this example is not an appropriate implementation).

After this process is complete, the daemon can sleep for `SEARCH_FREQUENCY_MINUTES` at which point it should wake and start this process again.

# Build system

The project will be hosted and built on Github.com. The project should include a Github Action workflow which builds the project and deploys the built image to support importing via `docker compose`.

Here is the relevant section of Github's docs on this subject: https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images

Ensure you check the documentation so that your work is correct. Each commit to `main` should result in a build job that rebuilds the image.