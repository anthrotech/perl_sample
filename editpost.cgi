#!/usr/local/bin/perl -w
# Point the above to your perl directory
###################################################################
# Edit Post
# Script Name: editpost.cgi
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
	use vars qw/%in %rec $rec $FORUMSDB $FORUMPOSTSDB $USERDB $USER %USER/;
	$|++;	

	&main();

sub main {
# ---------------------------------------------------
# Create CGI object and figure out what to do.
#
	my $in      = new CGI;
	my $dynamic = $in->param('d') ? $in : undef;
	%in         = %{&cgi_to_hash ($in)};
	my ($author, $cleanmess, $cleansub, $forum, $forumname, $forumid, $moderator, $notify, $poster, $postparentid, $sig, $username);
	my $postid = $in->param('ID');
	my $title_linked       = &build_linked_forum_title ("Edit Post");
	my $title_error_linked = &build_linked_forum_title ("Edit Post/Error: Unable to Process Form");

# Get user information.
	my $s = $in->param('s') || $in->cookie('s');
	$USER = &authenticate ($s);
	if (! defined $USER) {
		my $encurl = &Links::DBSQL::encode ("$CUSTOM{build_editpost_url}?$ENV{'QUERY_STRING'}");
		print $in->redirect("$CUSTOM{build_login_url}?to=$encurl") and return;            
	}          
	
# Check that the record hasn't been added already in the Links and Validate tables.	
	if ($postid =~ /^\d+$/) {
		my $postrec  = $FORUMPOSTSDB->get_record ($postid, 'HASH');
		($postrec) or print $in->redirect("$CUSTOM{build_forum_url}") and return;		    	
		$forumid      = $postrec->{ForumID};
		$postparentid = $postrec->{PostParentID};
		my $postmess  = $postrec->{PostMessage};
		my $postsub   = $postrec->{PostSubject};
     		$cleanmess    = &Links::DBSQL::clean_html($postmess);
     		$cleansub     = &Links::DBSQL::clean_html($postsub);
     		undef $Links::DBSQL::DBH;
		my $posterrec = $USERDB->get_record ($postrec->{PosterID}, 'HASH');		     		
		$author       = $posterrec->{Author};
		$username     = $posterrec->{Username};
		if (($author) and ($username)) {
			$poster = qq|$author|;
		}
		if ((!$author) and ($username)) {
			$poster = qq|$username|;
		}
		my $forumrec  = $FORUMSDB->get_record ($forumid, 'HASH');
		$moderator    = $forumrec->{ModeratorID};
		$forumname    = $forumrec->{ForumName};				
		if (($USER->{UserID} eq $postrec->{PosterID}) and ($postrec->{PostActive} eq 'Y') or ($USER->{UserID} eq $moderator) or ($USER->{Status} eq 'Administrator')) {
				if ($postrec->{PostNotify} eq 'Y') {
					$notify = qq|<input type="radio" name="PostNotify" value="Y" CHECKED> Yes <input type="radio" name="PostNotify" value="N"> No|;
				}
				elsif ($postrec->{PostNotify} eq 'N') {
					$notify = qq|<input type="radio" name="PostNotify" value="Y"> Yes <input type="radio" name="PostNotify" value="N" CHECKED> No|;
				}
				else {
					$notify = qq|<input type="radio" name="PostNotify" value="Y"> Yes <input type="radio" name="PostNotify" value="N"> No|;
				}
				if ($postrec->{PostSig} eq 'Y') {
					$sig = qq|<input type="radio" name="PostSig" value="Y" CHECKED> Yes <input type="radio" name="PostSig" value="N"> No|;
				}
				elsif ($postrec->{PostSig} eq 'N') {
					$sig = qq|<input type="radio" name="PostSig" value="Y"> Yes <input type="radio" name="PostSig" value="N" CHECKED> No|;
				}
				else {
					$sig = qq|<input type="radio" name="PostSig" value="Y"> Yes <input type="radio" name="PostSig" value="N"> No|;
				}
				if (($USER->{UserID} eq $moderator) or ($USER->{Status} eq 'Administrator')) {
					if ($postparentid == '0') {
						$forum = &get_forums_drop($forumid,"ForumID"); 
					}
					else {
						$forum = qq|<span class="text">$forumname</span> <input type="hidden" name="ForumID" value="$forumid"><input type="hidden" name="ForumName" value="$forumname">|;
					}
				}
				else {
					$forum = qq|<span class="text">$forumname</span> <input type="hidden" name="ForumID" value="$forumid"><input type="hidden" name="ForumName" value="$forumname">|;
				}
				print $in->header();
				&site_html_edit_post ({forum => $forum, OrigForumID => $forumid, ModeratorID => $moderator, Poster => $poster, PostID => $postid, PostParentID => $postparentid, Notify => $notify, Signature => $sig, PostMessage => $cleanmess, PostSubject => $cleansub, title_linked => $title_linked}, $dynamic) and return;
		}		
		else {
			print $in->header();
			&site_html_error ({error => "You do not have permission to edit this post.", title_linked => $title_error_linked}, $dynamic) and return;
		}
	}
	elsif ($in->param('edit_post')) {
        	print $in->header();
        	&edit_post ($in, $dynamic);
	}
	elsif ($in->param('delete_post')) {
        	print $in->header();
        	&delete_post ($in, $dynamic);
	}
	elsif ($in->param('delete_confirm')) {
        	print $in->header();
        	&delete_confirm ($in, $dynamic);
	}	
	elsif ($in->param('edit_confirm')) {
        	print $in->header();
        	&edit_confirm ($in, $dynamic);
	}
	else {
		print $in->redirect("$CUSTOM{build_forum_url}") and return;	
	}
}
# ==============================================================

sub delete_confirm {
#---------------------------------------------------------
# Confirms submissions before submitting.
     my ($in, $dynamic) = @_;
     my ($error, $found, $notifystatus, $notify_status, $sigstatus, $sig_status);
     my $postid    = $in->param('PostID');
     my $postsub    = $in->param('PostSubject');
     
     my $title_linked = &build_linked_forum_title ("Delete Post/Confirm Submission");
     &site_html_delete_post_confirm({PostID => $postid, title_linked => $title_linked}, $dynamic) and return;
}


sub delete_post {
# --------------------------------------------------------          
	my ($in, $dynamic) = @_;
	my ($mod_author, $moderator, $post_author, $timestamp, $key, $original); 
	my ($to, $from, $subject, $msg, $mailer);
	my $postid    = $in->param('PostID');
     	my $title_linked       = &build_linked_forum_title ("Delete Post/Post Successfully Deleted");	
	my $title_error_linked = &build_linked_forum_title ("Delete Post/Error: Unable to Process Form");  	

# Get the record.
        my $rec = $FORUMPOSTSDB->get_record ($postid, 'HASH');
        $rec or &site_html_error ({error => "Invalid Post!", title_linked => $title_error_linked}, $dynamic) and return;   

# Get Original Data

	foreach my $key (keys %$rec) {
		$original->{$key} = $rec->{$key};
		$rec->{$key} = $in->param($key) if ($in->param($key));
	}
	my $checkid    = $original->{CheckID};
	my $checkdel   = $original->{PostDelete};
	my $forumid    = $original->{ForumID};
	my $posterid   = $original->{PosterID};
	my $parentid   = $original->{PostParentID};
	my $postsub    = $original->{PostSubject};
	my $postmess   = $original->{PostMessage};
	my $postnotify = $original->{PostNotify};
	my $replies    = $original->{NumberReplies};
	my $add_date   = $original->{Add_Post};
	my $hits       = $original->{PostHits};

# Connect to Forum Topic table
        my $forumrec  = $FORUMSDB->get_record ($forumid, 'HASH');
        $forumrec or &site_html_error ({error => "Invalid Forum!", title_linked => $title_error_linked}, $dynamic) and return;
        my $forumname = $forumrec->{ForumName};
        
# Set date variable to today's date.
      $timestamp = $FORUMPOSTSDB->get_datetime();	
      
# Get User information
			
# Add to Cover Letter table
        $FORUMPOSTSDB->do ("UPDATE Forum_Posts
        		SET 
     		      	PostID        = '$postid',
     		      	CheckID       = '$checkid',
      		      	ForumID       = '$forumid',
      		      	PostParentID  = '$parentid',
      		      	PosterID      = '$posterid',
      		      	NumberReplies = '$replies',
      		      	PostSubject   = '$postsub',
      		      	PostMessage   = '$postmess',
      		      	PostActive    = 'N',
      		      	PostNotify    = '$postnotify',
      		      	PostDelete    = 'Y',
      		      	PostSig       = 'N',
      		      	Add_Post      = '$add_date',
      		      	Mod_Post      = '$timestamp',
      		      	PostUpdated   = '$timestamp',
      		      	PostHits      = '$hits'
      		      	WHERE PostID  = $postid
        		
        ");
        if ($checkdel eq 'N') {
        	$FORUMSDB->do ("UPDATE Forum_Topics
        		SET 
        		NumberPosts  = NumberPosts - 1,
        		Last_Updated = '$timestamp'
        		WHERE ForumID = $forumid
        	");        
        	undef $Links::DBSQL::DBH;
        	$USERDB->do ("UPDATE Users
        		SET 
        		ForumPosts = ForumPosts - 1
        		WHERE UserID = $postid
        	");
        }
	&site_html_delete_post_success ({ForumID => $forumid, ForumName => $forumname, title_linked => $title_linked}, $dynamic);
	return;
}

sub edit_confirm {
#---------------------------------------------------------
# Confirms submissions before submitting.
     my ($in, $dynamic) = @_;
     my ($cleanmess, $cleanmessview, $cleansub, $cleansubview, $error, $forum, $printforum, $found, $notifystatus, $notify_status, $sigstatus, $sig_status);
     my $forumid       = $in->param('ForumID');
     my $moderator     = $in->param('ModeratorID');
     my $origforumid   = $in->param('OrigForumID');
     my $poster        = $in->param('Poster');
     my $forumname     = $in->param('ForumName');
     my $postid        = $in->param('PostID');
     my $postsub       = $in->param('PostSubject');
     my $postmess      = $in->param('PostMessage');
     my $postnotify    = $in->param('PostNotify');
     my $postparentid  = $in->param('PostParentID');
     my $postsig       = $in->param('PostSig');
     
# Check blank fields
	if (!$postsub) {
		$error .= "<li>You must submit a <span class=\"boldredtext\">Post Subject</span>.</li><br>";
	}  
	if (!$postmess) {
		$error .= "<li>You must submit a <span class=\"boldredtext\">Message</span>.</li><br>";
	} 
	if (!$postnotify) {
		$error .= "<li>You must select an <span class=\"boldredtext\">Email Notification Permission</span>.</li><br>";
	}  	
	if (!$postsig) {
		$error .= "<li>You must select a <span class=\"boldredtext\">Signature Permission</span>.</li><br>";
	}  		
	if ($postnotify eq 'Y') {
		$notifystatus .= qq|<input type="radio" name="PostNotify" value="Y" CHECKED> Yes
		<input type="radio" name="PostNotify" value="N"> No|;
		$notify_status = qq|<span class="text">Yes <input type="hidden" name="PostNotify" value="Y"></span>|;
	}	
	if ($postnotify eq 'N') {
		$notifystatus .= qq|<input type="radio" name="PostNotify" value="Y"> Yes
		<input type="radio" name="PostNotify" value="N" CHECKED> No|;
		$notify_status = qq|<span class="text">No <input type="hidden" name="PostNotify" value="N"></span>|;
	}
	if ($postnotify eq ""){
	        $notifystatus .= qq|<input type="radio" name="PostNotify" value="Y"> Yes
		<input type="radio" name="PostNotify" value="N"> No|;
		$notify_status = "Not Specified";
        } 	
	if ($postsig eq 'Y') {
		$sigstatus .= qq|<input type="radio" name="PostSig" value="Y" CHECKED> Yes
		<input type="radio" name="PostSig" value="N"> No|;
		$sig_status = qq|<span class="text">Yes <input type="hidden" name="PostSig" value="Y"></span>|;
	}	
	if ($postsig eq 'N') {
		$sigstatus .= qq|<input type="radio" name="PostSig" value="Y"> Yes
		<input type="radio" name="PostSig" value="N" CHECKED> No|;
		$sig_status = qq|<span class="text">No <input type="hidden" name="PostSig" value="N"></span>|;
	}
	if ($postsig eq ""){
	        $sigstatus .= qq|<input type="radio" name="PostSig" value="Y"> Yes
		<input type="radio" name="PostSig" value="N"> No|;
		$sig_status = "Not Specified";
        }         
	if ($error) {
	     chomp($error);
	     if (($postparentid == '0') and ($USER->{UserID} eq $moderator) or ($USER->{Status} eq 'Administrator')) {
		     $forum = &get_forums_drop($forumid,"ForumID");
	     }
	     else {
		     $forum = qq|<span class="text">$forumname</span> <input type="hidden" name="ForumID" value="$forumid"><input type="hidden" name="ForumName" value="$forumname">|; 
	     }			     
             my $title_error_linked = &build_linked_forum_title ("Edit Post/Error: Unable to Process Form");
             &site_html_edit_post_failure({forum => $forum, OrigForumID => $origforumid, Poster => $poster, PostID => $postid, PostParentID => $postparentid, PostSubject => $postsub, PostMessage => $postmess, Notify => $notifystatus, Signature => $sigstatus, error => $error, title_linked => $title_error_linked}, $dynamic);
             return;
        }
        else { 
              $printforum    = &get_forums_name($forumid);
              $cleanmess     = &Links::DBSQL::clean_html($postmess);
              $cleanmessview = &Links::DBSQL::clean_markup($postmess); 
	      $cleansub      = &Links::DBSQL::clean_html($postsub);
	      $cleansubview  = &Links::DBSQL::clean_markup($postsub);              
              my $title_linked = &build_linked_forum_title ("Edit Post/Confirm Submission");
              &site_html_edit_post_confirm({
              ForumName => $printforum, 
              ForumID => $forumid, 
              OrigForumID => $origforumid, 
              Poster => $poster, 
              PostParentID => $postparentid,
              ModeratorID => $moderator,
              PostID => $postid,  
              PostSubject => $cleansub, 
              ShowSubject => $cleansubview, 
              PostMessage => $cleanmess, 
              ShowMessage => $cleanmessview, 
              PostNotify => $notify_status, 
              PostSig => $sig_status, 
              title_linked => $title_linked}, $dynamic);
              return;
        }
}

sub edit_post {
# --------------------------------------------------------          
	my ($in, $dynamic) = @_;
	my ($cleanmess, $cleansub, $timestamp, $id, $key, $mod_author, $modedited, $modrec, $original); 
	my ($to, $from, $subject, $msg, $mailer);
	my $forumid     = $in->param('ForumID'); 
	my $origforumid = $in->param('OrigForumID'); 
	my $postid      = $in->param('PostID');
     	my $postsub     = $in->param('PostSubject');
     	my $postmess    = $in->param('PostMessage');
     	my $postnotify  = $in->param('PostNotify');
     	my $postsig     = $in->param('PostSig');
     	my $title_linked       = &build_linked_forum_title ("Edit Post/Post Successfully Edited");	
	my $title_error_linked = &build_linked_forum_title ("Edit Post/Error: Unable to Process Form");  	

# Set date variable to today's date.
        $timestamp = $FORUMPOSTSDB->get_datetime();
      
# Get the record.
        my $rec = $FORUMPOSTSDB->get_record ($postid, 'HASH');
        $rec or &site_html_error ({error => "Invalid Post!", title_linked => $title_error_linked}, $dynamic) and return;   
        
# Get Original Data

	foreach my $key (keys %$rec) {
		$original->{$key} = $rec->{$key};
		$rec->{$key} = $in->param($key) if ($in->param($key));
	}
	
	my $checkid    = $original->{CheckID};
	my $posterid   = $original->{PosterID};
	my $parentid   = $original->{PostParentID};
	my $active     = $original->{PostActive};
	my $replies    = $original->{NumberReplies};
	my $add_date   = $original->{Add_Post};
	my $hits       = $original->{PostHits};
	my $updated    = $original->{PostUpdated};	

# Connect to Forums Table
       my $forumrec  = $FORUMSDB->get_record ($forumid, 'HASH');
       $forumrec or &site_html_error ({error => "Invalid Forum!", title_linked => $title_error_linked}, $dynamic) and return;   
       my $forumname = $forumrec->{ForumName};
        
# Add to Forum Posts table
       $in->param ( -name => 'PostID', -value => $postid);	
       $in->param ( -name => 'CheckID', -value => $checkid);
       $in->param ( -name => 'ForumID', -value => $forumid);
       $in->param ( -name => 'PostParentID', -value => $parentid);
       $in->param ( -name => 'PosterID', -value => $posterid);
       $in->param ( -name => 'NumberReplies', -value => $replies);
       $in->param ( -name => 'PostSubject', -value => $postsub);
       $in->param ( -name => 'PostMessage', -value => $postmess);
       $in->param ( -name => 'PostActive', -value => $active);
       $in->param ( -name => 'PostNotify', -value => $postnotify);
       $in->param ( -name => 'PostDelete', -value => 'N');
       $in->param ( -name => 'PostSig', -value => $postsig);
       $in->param ( -name => 'Add_Post', -value => $add_date);
       $in->param ( -name => 'Mod_Post', -value => $timestamp);
       $in->param ( -name => 'PostUpdated', -value => $timestamp);
       $in->param ( -name => 'PostHits', -value => $hits);
       $id = $FORUMPOSTSDB->modify_record (&cgi_to_hash($in));
     
       if ($origforumid ne $forumid) {        
       		my $getchildposts = $FORUMPOSTSDB->query({PostParentID => $postid, ww => 1});
       		my $getchildhits  = $FORUMPOSTSDB->hits;
       		my $totalhits     = $getchildhits + 1;
       		if ($getchildhits) {
       				$FORUMPOSTSDB->do ("UPDATE Forum_Posts
        				SET 
        				ForumID = $forumid
        				WHERE (PostParentID = $postid)
       				");          		
       				$FORUMSDB->do ("UPDATE Forum_Topics
        				SET 
        				NumberPosts = NumberPosts - $totalhits 
        				WHERE (ForumID = $origforumid)
       				");
       				$FORUMSDB->do ("UPDATE Forum_Topics
        				SET 
        				NumberPosts = NumberPosts + $totalhits
        				WHERE (ForumID = $forumid)
       				");   
       		}
       		else {    		
       			$FORUMSDB->do ("UPDATE Forum_Topics
        			SET 
        			NumberPosts = NumberPosts - 1 
        			WHERE (ForumID = $origforumid)
       			");
       			$FORUMSDB->do ("UPDATE Forum_Topics
        			SET 
        			NumberPosts = NumberPosts + 1
        			WHERE (ForumID = $forumid)
       			");     
       		}
       }
       $FORUMSDB->do ("UPDATE Forum_Topics
               		SET 
               		Last_Updated = '$timestamp'
               		WHERE (ForumID = $forumid) AND (ForumID =  $origforumid)
       ");
       
       $cleanmess = &Links::DBSQL::clean_markup($postmess);
       $cleansub  = &Links::DBSQL::clean_markup($postsub);	
       &site_html_edit_post_success ({ForumID => $forumid, ForumName => $forumname, PostID => $postid, PostSubject => $cleansub, PostMessage => $cleanmess, PostNotify => $postnotify, PostSig => $postsig, title_linked => $title_linked}, $dynamic);
       return;
}