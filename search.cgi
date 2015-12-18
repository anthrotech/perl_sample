#!/usr/local/bin/perl -w
# Point the above to your perl directory
###################################################################
# Search Forums
# Script Name: search.cgi
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
	use Links::DBSQL;
	use Links::DB_Utils;
	use Links::Forum_HTML_Templates;
	use Links::Globals;
	use Links::Members;
        my $FORUMPOSTSDB   = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Posts.def";
        my $FORUMSDB       = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Topics.def";     
        my $USERDB         = new Links::DBSQL $CUSTOM{members_def}  . "Users.def";
	use vars qw/%in %rec $rec $FORUMPOSTSDB $FORMSDB $USERDB $USER %USER/;
	$|++;	

	&main();

sub main {
# ---------------------------------------------------
# Determine what to do.
#
	my $in = new CGI;
	my $dynamic = $in->param('d') ? $in : undef;
	%in    = %{&cgi_to_hash($in)};     
 
        if ($in->param('search')) {
              print $in->header();   
              &search ($in, $dynamic);
        }      
        elsif ($in->param('UserID')) {
              &searchuser ($in, $dynamic);
        }
	else  { 
	      print $in->header();   
	      &display ($in, $dynamic); 
	}
}
# ==============================================================

sub display {
# --------------------------------------------------------
      my ($in, $dynamic) = @_;
      my $forum = &get_forums_search_list ('',"ForumID");   
      my ($userposts);
      my $s = $in->param('s') || $in->cookie('s');
      $USER = &authenticate ($s);
      if (defined $USER) {
      	   $userposts = qq|
      	   <tr>
      	   <td valign="top" width="50%" bgcolor="FFFFCC">
      	   <span class="subheader">Search My Posts ONLY</span>
      	   </td>
      	   <td valign="top" width="50%" bgcolor="EEEEEE">
      	   <span class="text">      	   
      	   <input type="checkbox" name="UserID" value="myposts"> Yes
      	   </span>
      	   </td></tr>
      	   |;
      }
      my $title_linked = &build_linked_forum_title ("Search Forums");
      &site_html_search_forum_form ({Forums => $forum, userposts => $userposts, title_linked => $title_linked}, $dynamic);

}

sub search {
# --------------------------------------------------------
	my ($in, $dynamic) = @_;
	my ($add_post, $author, $forummoderator, $forumstatus, $forumname, $forumid, $forum_select, $mod_post, $order, $orderby, $postactive, $postid, $posterid, $posts, $postsub, $query, $recs, $sqlquery, $sth, $span, $userperm, $where, $user_posts);
	my $forum_choose  = $in->param('ForumID');
	my $keywords      = $in->param('Keywords');
	my $days          = $in->param('Days');
	my $option        = $in->param('Option');
	my $userposts     = $in->param('UserID');
	my $sb            = $in->param('sb');
	my $so            = $in->param('so');
      	my $s = $in->param('s') || $in->cookie('s');
        $USER = &authenticate ($s);	

# Get the user's links.
	$query = qq!
			SELECT Forum_Posts.*
			FROM Forum_Posts
			WHERE (PostActive = 'Y')
	!;
	if ($forum_choose ne "") {
		$where = qq| AND (ForumID = $forum_choose)|;
	}
	if (($keywords ne "") and ($option eq 'any')) {
		$where = qq| AND (PostSubject LIKE '%$keywords%') AND (Forum_Posts.PostMessage LIKE '%$keywords%')|;
	}
	if (($keywords ne "") and ($option eq 'and')) {
		$where = qq| AND (PostSubject = '%$keywords%') AND (Forum_Posts.PostMessage = '%$keywords%')|;
	}
	if ($days ne "") {
		$where = qq| AND (Add_Post > DATE_SUB(NOW(), INTERVAL $days DAY))|;
	}
	if ((defined $USER) and ($userposts eq "myposts")) {
		$where = qq| AND (PosterID = $USER->{UserID})|;
	}	
	if ($sb eq 'addpost') {
		$order = qq| ORDER BY Add_Post|;
	}
	if ($sb eq 'subject') {
		$order = qq| ORDER BY PostSubject|;
	}		
	if ($so eq 'asc') {
		$orderby = qq| ASC|;
	}
	if ($so eq 'desc') {
		$orderby = qq| DESC|;
	}
	if ($where) {
	      $sqlquery = ($query . $where . $order . $orderby);
	}
	else {
	      $sqlquery = ($query . $order . $orderby);  
	}
	$sth = $FORUMPOSTSDB->prepare($sqlquery);
	$sth->execute() or die $DBI::errstr;
	my $hits = $sth->rows();
	my ($rec, $output);
		while ($rec = $sth->fetchrow_hashref) {
			$postid      = $rec->{'PostID'};
			$posterid    = $rec->{'PosterID'};
			$forumid     = $rec->{'ForumID'};
			$add_post    = $rec->{'Add_Post'};
			$mod_post    = $rec->{'Mod_Post'};
			$postsub     = $rec->{'PostSubject'};
			$postactive  = $rec->{'PostActive'};
      		        my $getforum = $FORUMSDB->get_record ($forumid, 'HASH');
      		        foreach (keys %$getforum) { 
      		        	$forumname   = $getforum->{ForumName};
      		        	$forumstatus    = $getforum->{ForumStatus};
      		        	$forummoderator = $getforum->{ForumModerator};
      		        }			
			$forumname = &get_forums_name($forumid);
      			undef $Links::DBSQL::DBH;
			my $poster   = $USERDB->get_record ($posterid, 'HASH');
			foreach (keys %$poster) { 
				$author    =  $poster->{Author};
				$userperm  =  $poster->{Username_Permission};
			}
			$posts .= &site_html_post_newlink ({Add_Post => $add_post, Author => $author, ForumID => $forumid, ForumName => $forumname, ForumModerator => $forummoderator, ForumStatus => $forumstatus, Mod_Post => $mod_post, PostID => $postid, PosterID => $posterid, PostActive => $postactive, PostSubject => $postsub, Username_Permission => $userperm});
	}		
        if ($hits) {
# Display the page.
	     ($FORUMPOSTSDB->hits > $CUSTOM{forum_span}) and ($span = $FORUMPOSTSDB->toolbar(search => '1'));
      	     my $title_linked = &build_linked_forum_title ("Search Forums/Search Results");
      	     &site_html_search_forum_success ({query => $sqlquery, Posts => $posts, span => $span, title_linked => $title_linked}, $dynamic);
      	     exit;
      	}
      	else {
      	    if (defined $USER) {
      	   	if ($userposts eq 'myposts') {
      	   		$user_posts = qq|
      	   		<tr>
      	   		<td valign="top" width="50%" bgcolor="FFFFCC">
      	   		<span class="subheader">Search My Posts ONLY</span>
      	   		</td>
      	   		<td valign="top" width="50%" bgcolor="EEEEEE">
      	   		<span class="text">      	   
      	   		<input type="checkbox" name="UserID" value="myposts" CHECKED> Yes
      	   		</span>
      	   		</td></tr>
      	   		|;
      	        }
      	        else {
      	   		$user_posts = qq|
      	   		<tr>
      	   		<td valign="top" width="50%" bgcolor="FFFFCC">
      	   		<span class="subheader">Search My Posts ONLY</span>
      	   		</td>
      	   		<td valign="top" width="50%" bgcolor="EEEEEE">
      	   		<span class="text">      	   
      	   		<input type="checkbox" name="UserID" value="myposts"> Yes
      	   		</span>
      	   		</td></tr>
      	   		|;
      	     	}
      	     }
	     $forum_select    = &get_forums_list ($in->param('ForumID'),"ForumID");
	     my $title_linked = &build_linked_forum_title ("Search Forums/Error: Unable to Process Form");
	     &site_html_search_forum_failure  ({userposts => $user_posts, query => $sqlquery, Forums => $forum_select, Keywords => $keywords, error => "There are no posts that match your selection.", title_linked => $title_linked}, $dynamic);
	     exit;      	     
      	}
}

sub searchuser {
# --------------------------------------------------------
	my ($in, $dynamic) = @_;
	my ($add_post, $author, $forummoderator, $forumstatus, $forumname, $forumid, $forum_select, $mod_post, $order, $orderby, $postactive, $postid, $posterid, $posts, $postsub, $query, $recs, $sth, $span, $userperm);
	my $userid  = $in->param('UserID');

	if ($userid  =~ /^\d+$/) {
# Get the user's links.
		$query = qq!
			SELECT Forum_Posts.*
			FROM Forum_Posts
			WHERE (PostActive = 'Y') AND (PosterID = $userid)
			ORDER BY Add_Post DESC
		!;
		$sth = $FORUMPOSTSDB->prepare($query);
		$sth->execute() or die $DBI::errstr;
		my $hits = $sth->rows();
		my ($rec, $output);
		while ($rec = $sth->fetchrow_hashref) {
			$postid      = $rec->{'PostID'};
			$posterid    = $rec->{'PosterID'};
			$forumid     = $rec->{'ForumID'};
			$add_post    = $rec->{'Add_Post'};
			$mod_post    = $rec->{'Mod_Post'};
			$postsub     = $rec->{'PostSubject'};
			$postactive  = $rec->{'PostActive'};
      		        my $getforum = $FORUMSDB->get_record ($forumid, 'HASH');
      		        foreach (keys %$getforum) { 
      		        	$forumname   = $getforum->{ForumName};
      		        	$forumstatus    = $getforum->{ForumStatus};
      		        	$forummoderator = $getforum->{ForumModerator};
      		        }			
			$forumname = &get_forums_name($forumid);
      			undef $Links::DBSQL::DBH;
			my $poster   = $USERDB->get_record ($posterid, 'HASH');
			foreach (keys %$poster) { 
				$author    =  $poster->{Author};
				$userperm  =  $poster->{Username_Permission};
			}
			$posts .= &site_html_post_newlink ({Add_Post => $add_post, Author => $author, ForumID => $forumid, ForumName => $forumname, ForumModerator => $forummoderator, ForumStatus => $forumstatus, Mod_Post => $mod_post, PostID => $postid, PosterID => $posterid, PostActive => $postactive, PostSubject => $postsub, Username_Permission => $userperm});
	}		
        	if ($hits) {
# Display the page.
		     ($FORUMPOSTSDB->hits > $CUSTOM{forum_span}) and ($span = $FORUMPOSTSDB->toolbar(search => '1'));
      		     print $in->header(); 
      		     my $title_linked = &build_linked_forum_title ("Search Forums/Search Results");
      		     &site_html_search_forum_success ({query => $query, Posts => $posts, span => $span, title_linked => $title_linked}, $dynamic);
      		     exit;
      		}
      		else {
      		     print $in->header(); 
		     my $title_linked = &build_linked_forum_title ("Search Forums/Error: Unable to Process Form");
		     &site_html_error  ({error => "User has not posted any topics in our discussion forum.", title_linked => $title_linked}, $dynamic);
		     exit;      	     
      		}
      	}
      	else {
      	       print $in->redirect("$CUSTOM{build_forum_url}") and return;      	   
      	}
}