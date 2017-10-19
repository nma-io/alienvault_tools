# Generic scripts/tools to help with general Alienvault OSSIM stuff.
*Nothing* should be considered 'Production Quality' or approved by Alienvault.


All items are provided without warranty. Try in your lab environment first.

* Much of this is from reading through the code I have access to. 
* I probably got things wrong and items may corrupt your databases or break processes.
* I could definitely tighten the code up and make it faster. Much of this is for quick 'break fixes' 
* I will revisit the code periodically if needed.

License is always BSD 2 - Feel free to use however you see fit.


Applications:  

otx_cleanup.py  ==  Add Post Processing whitelist and remove observables from older pulses - Run as a cronjob?

purge_old_assets.py == Remove older assets from the datastore - Run as cronjob

update_all_the_scan_things.sh == Will update all of the scanning related tools (including GEOIP, Nikto, OpenVAS and NMAP)

check_for_span.py == I uses this in a daily status check script in some customer environments. Quickly identify which interface is running the span.


