#!/usr/local/bin/perl -w
# Point the above to your perl directory
###################################################################
# Forum Announcement Script
# Script Name: announcements.cgi
# Copyright 2001, Anthro TECH
# http://www.anthrotech.com/
# info@anthrotech.com
# 
# DISCLAIMER: This script may not be re-distributed without the 
# written consent of Anthro TECH. This script may not be sold for
# any reason.
###################################################################

# Load required modules.
# ---------------------------------------------------
	use strict;
	use CGI ();
	use CGI::Carp qw/fatalsToBrowser/;
	use lib '/home/anthrotech/www/cgibin/admin';
	use Links::Custom;
	use Links::Date;
	use Links::DBSQL;
	use Links::DB_Utils;
	use Links::Forum_HTML_Templates;
	use Links::Globals;
	use Links::Members;
        my $FORUMPOSTSDB   = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Posts.def";
  	use vars qw/%in %rec $rec $FORUMPOSTSDB $USER %USER/;
	$|++;	

	&main();

sub main {
# ---------------------------------------------------
# Determine what to do.
#
	my $in = new CGI;
	my $dynamic = $in->param('d') ? $in : undef;
	%in    = %{&cgi_to_hash($in)};
	&display ($in, $dynamic);
}

sub display {
# --------------------------------------------------------
      my ($in, $dynamic) = @_;
      my ($posts, $sth);
      $sth = $FORUMPOSTSDB->prepare ("SELECT Forum_Posts.* 
      				      FROM Forum_Posts 
      				      WHERE (Forum_Posts.ForumID = '13') AND 
      				      	    (Forum_Posts.Expire_Post IS NOT NULL) AND 
      				      	    (Forum_Posts.Expire_Post BETWEEN NOW() AND Forum_Posts.Expire_Post) 
      				      ORDER BY Forum_Posts.Mod_Post DESC LIMIT 3
      ");
      $sth->execute() or die $DBI::errstr;
      while (my $postrec = $sth->fetchrow_hashref) {
		$posts .= &site_html_forum_newslink ({%$postrec});
      }      
      &site_html_forum_news ({Posts => $posts}, $dynamic);		      
}