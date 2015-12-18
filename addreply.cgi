#!/usr/local/bin/perl -w
# Point the above to your perl directory
###################################################################
# Add Reply
# Script Name: addreply.cgi
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
# Create CGI object and figure out what to do.
#
	my $in      = new CGI;
	my $dynamic = $in->param('d') ? $in : undef;
	%in         = %{&cgi_to_hash ($in)};
	my ($cleanparentmess, $cleanparentsub, $forumid, $moderatorid, $notify, $postactive, $parentid, $parentmess, $parentsub, $sig, $userid);
	my $postid  = $in->param('ID');
	my $code  = (time) . ($$) . (int rand (1000));
	my $title_linked       = &build_linked_forum_title ("Add Reply");
	my $title_error_linked = &build_linked_forum_title ("Add Reply/Error: Unable to Process Form");

# Get user information.
	my $s = $in->param('s') || $in->cookie('s');
	$USER = &authenticate ($s);
	if (! defined $USER) {
		my $encurl = &Links::DBSQL::encode ("$CUSTOM{build_addreply_url}?$ENV{'QUERY_STRING'}");
		print $in->redirect("$CUSTOM{build_login_url}?to=$encurl") and return;            
	}          
	
# Check that the record hasn't been added already in the Links and Validate tables.	
	if ($postid =~ /^\d+$/) {
		my $postrec      = $FORUMPOSTSDB->get_record ($postid, 'HASH');
		$forumid         = $postrec->{'ForumID'};
		$postid          = $postrec->{'PostID'};
		$postactive      = $postrec->{'PostActive'};
		$parentid        = $postrec->{'PostParentID'};
		$parentsub       = $postrec->{'PostSubject'};
		$parentmess      = $postrec->{'PostMessage'};
		$cleanparentmess = &Links::DBSQL::clean_markup($parentmess);
		$cleanparentsub  = &Links::DBSQL::clean_markup($parentsub);
		my $forumrec = $FORUMSDB->get_record ($forumid, 'HASH');
		$moderatorid = $forumrec->{ModeratorID};
		undef $Links::DBSQL::DBH;
		my $userrec  = $USERDB->get_record ($moderatorid, 'HASH');
		$userid      = $userrec->{UserID};
		if ($USER->{ForumNotify} eq 'Y') {
			$notify = qq|<input type="radio" name="PostNotify" value="Y" CHECKED> Yes
			<input type="radio" name="PostNotify" value="N"> No|;
		}
		if ($USER->{ForumNotify} eq 'N') {
			$notify = qq|<input type="radio" name="PostNotify" value="Y"> Yes
			<input type="radio" name="PostNotify" value="N" CHECKED> No|;
		}	
		if ($USER->{ForumSig} eq 'Y') {
			$sig = qq|<input type="radio" name="PostSig" value="Y" CHECKED> Yes
			<input type="radio" name="PostSig" value="N"> No|;
		}
		if ($USER->{ForumSig} eq 'N') {
			$sig = qq|<input type="radio" name="PostSig" value="Y"> Yes
			<input type="radio" name="PostSig" value="N" CHECKED> No|;
		}			
		if (($postrec) and ($postactive eq 'Y'))  {
			print $in->header();
			my $title_linked       = &build_linked_forum_title ("Add Reply/$parentsub");
			&site_html_add_reply ({CheckID => $code, notify => $notify, sig => $sig, ForumID => $forumid, PostID => $postid, PostParentID => $parentid, ParentSub => $cleanparentsub, ParentMess => $cleanparentmess, %in, title_linked => $title_linked}, $dynamic) and return;
		}
		elsif (($USER->{Status} eq 'Administrator') or ($USER->{UserID} eq $userid)) {
			print $in->header();
			my $title_linked       = &build_linked_forum_title ("Add Reply/$parentsub");
			&site_html_add_reply ({CheckID => $code, notify => $notify, sig => $sig, ForumID => $forumid, PostID => $postid, PostParentID => $parentid, ParentSub => $cleanparentsub, ParentMess => $cleanparentmess, %in, title_linked => $title_linked}, $dynamic) and return;		
		}
		else {
			print $in->header();
			my $title_error_linked = &build_linked_forum_title ("Add Reply/Error: Unable to Process Form");
			&site_html_error ({error => "You cannot reply to this thread.", title_linked => $title_error_linked}, $dynamic) and return;
		}
	}
	elsif ($in->param('add')) {
        	print $in->header();
        	&process_form ($in, $dynamic);
	}
	elsif ($in->param('confirm')) {
        	print $in->header();
        	&confirm_form ($in, $dynamic);
	}
	else {
		print $in->redirect("$CUSTOM{build_forum_url}") and return;	
	}
}
# ==============================================================

sub confirm_form {
#---------------------------------------------------------
# Confirms submissions before submitting.
     my ($in, $dynamic) = @_;
     my ($cleanparent, $cleanmess, $cleanmessview, $cleansub, $cleansubview, $error, $found, $parentmess, $notifystatus, $notify_status, $sigstatus, $sig_status);
     my $checkid          = $in->param('CheckID');
     my $forumid          = $in->param('ForumID');
     my $parentpostid     = $in->param('PostParentID');
     my $postid           = $in->param('PostID');
     my $postsub          = $in->param('PostSubject');
     my $postmess         = $in->param('PostMessage');
     my $postnotify       = $in->param('PostNotify');
     my $postsig          = $in->param('PostSig');
     
     my $postrec  = $FORUMPOSTSDB->get_record ($postid, 'HASH');
     $parentmess  = $postrec->{'PostMessage'};    
     $cleanparent = &Links::DBSQL::clean_markup($parentmess); 		

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
             my $title_error_linked = &build_linked_forum_title ("Add Reply/Error: Unable to Process Form");
             &site_html_add_reply_failure({CheckID => $checkid, ForumID => $forumid, ParentMess => $cleanparent, PostID => $postid, PostParentID => $parentpostid, PostSubject => $postsub, PostMessage => $postmess, PostNotify => $notifystatus, PostSig => $sigstatus, error => $error, title_linked => $title_error_linked}, $dynamic);
             return;
        }
        else {
	      $cleanmess     = &Links::DBSQL::clean_html($postmess);
	      $cleanmessview = &Links::DBSQL::clean_markup($postmess);
	      $cleansub      = &Links::DBSQL::clean_html($postsub);
	      $cleansubview  = &Links::DBSQL::clean_markup($postsub);	      
              my $title_linked = &build_linked_forum_title ("Add Reply/Confirm Submission");
              &site_html_add_reply_confirm({CheckID => $checkid, ForumID => $forumid, PostID => $postid, PostSubject => $cleansub, ShowSubject => $cleansubview, PostParentID => $parentpostid, PostMessage => $cleanmess, ShowMessage => $cleanmessview, PostNotify => $notify_status, PostSig => $sig_status, title_linked => $title_linked}, $dynamic);
              return;
        }
}

sub process_form {
# --------------------------------------------------------          
	my ($in, $dynamic) = @_;
	my ($checkpost, $checkpost_hits, $cleanmess, $cleansub, $timestamp, $id, $key, $rec, $password, $putpostid, $postparentid, $posterid, $post_notify, $postername, $username, $useremail, $replierid); 
	my ($to, $from, $subject, $msg, $mailer);
	my $checkid     = $in->param('CheckID');
	my $forumid      = $in->param('ForumID');
	my $parentpostid = $in->param('PostParentID');
	my $postid       = $in->param('PostID');
     	my $postsub      = $in->param('PostSubject');
     	my $postmess     = $in->param('PostMessage');
     	my $postnotify   = $in->param('PostNotify');
     	my $postsig      = $in->param('PostSig');
     	my $title_linked       = &build_linked_forum_title ("Add Reply/Post Successfully Added");	
	my $title_error_linked = &build_linked_forum_title ("Add Reply/Error: Unable to Process Form");  	

# Check CheckID for duplicate post
        $checkpost      = $FORUMPOSTSDB->query ({CheckID => $checkid, mh => 1, ww => 1});
        $checkpost_hits = $FORUMPOSTSDB->hits;
        if ($checkpost_hits) {
            &site_html_error ({error => "You have already submitted your reply.", title_linked => $title_error_linked}, $dynamic);
            return;
        }

# Check Parent Post ID
 	if ($parentpostid eq '0') {
 		$putpostid = $postid;
 	}
 	else {
 		$putpostid = $parentpostid;
 	}

# Connect to Username database and obtain Email Address for Username
         $replierid  = $USER->{UserID};
         $useremail  = $USER->{Email};
         $postername = $USER->{Username};
         $password   = $USER->{Password};

         my $postrec  = $FORUMPOSTSDB->get_record ($postid, 'HASH');
         $posterid     = $postrec->{'PosterID'};
         $post_notify  = $postrec->{'PostNotify'};
         
         my $forumrec    = $FORUMSDB->get_record ($forumid, 'HASH');
         my $forumname      = $forumrec->{'ForumName'};  
         my $forumstatus    = $forumrec->{'ForumStatus'}; 
         my $forummoderator = $forumrec->{'ForumModerator'}; 
         my $forumnotify    = $forumrec->{'ForumNotify'};
         
         undef $Links::DBSQL::DBH;
         my $userrec  = $USERDB->get_record ($posterid, 'HASH');
         $username    = $userrec->{'Username'};
         $useremail   = $userrec->{'Email'};
         $password    = $userrec->{'Password'};
				
# Set date variable to today's date.
         $timestamp = $FORUMPOSTSDB->get_datetime();
	
# Add to Forum Posts table

       $in->param ( -name => 'ForumID', -value => $forumid);
       $in->param ( -name => 'PostParentID', -value => $putpostid);
       $in->param ( -name => 'PosterID', -value => $replierid);
       $in->param ( -name => 'NumberReplies', -value => '0');
       $in->param ( -name => 'PostSubject', -value => $postsub);
       $in->param ( -name => 'PostMessage', -value => $postmess);
       $in->param ( -name => 'PostActive', -value => 'Y');
       $in->param ( -name => 'PostNotify', -value => $postnotify);
       $in->param ( -name => 'PostDelete', -value => 'N');
       $in->param ( -name => 'PostSig', -value => $postsig);
       $in->param ( -name => 'Add_Post', -value => $timestamp);
       $in->param ( -name => 'Mod_Post', -value => $timestamp);
       $in->param ( -name => 'PostUpdated', -value => $timestamp);
       $in->param ( -name => 'PostHits', -value => '0');
       $rec = &cgi_to_hash($in);
       $id  = $FORUMPOSTSDB->add_record ($rec, $in);

        $FORUMSDB->do ("UPDATE Forum_Topics
        		SET 
        		NumberPosts  = NumberPosts + 1,
        		Last_Updated = '$timestamp'
        		WHERE ForumID = $forumid
        ");
        $FORUMPOSTSDB->do ("UPDATE Forum_Posts
        		SET 
        		NumberReplies  = NumberReplies + 1,
        		PostUpdated    = '$timestamp'
        		WHERE PostID   = $putpostid
        ");   
        undef $Links::DBSQL::DBH;
        $USERDB->do ("UPDATE Users
        	      SET ForumPosts = ForumPosts + 1
        	      WHERE UserID = $replierid
        ");              
        
if (($forumstatus eq 'Private') and ($forummoderator eq 'N') and ($replierid ne '103')) {
# Send Email to User
# Check to make sure that there is an admin email address defined.
	    $CUSTOM{db_forum_email} or die ("Admin Email Address Not Defined in config file!");
	    $to      = $CUSTOM{db_forum_email};
	    $from    = $useremail;
	    $subject = "Post added to $FORUM{build_site_title}\n";
	    $msg     = qq|
Dear Forum Administrator,

A reply was added to the following post:

$CUSTOM{build_forum_url}?showtopic=$postid

Please check it out when you get a chance.

Regards,

Eliot Lee
Founder and Editor
Anthro TECH, L.L.C 
$FORUM{build_site_title}
$CUSTOM{build_forum_url}
$CUSTOM{db_forum_email}
|;     

# Then mail it away!    
	    require Links::Mailer;
		$mailer = new Links::Mailer ( { 
				 smtp => $CUSTOM{db_smtp_server}, 
                                 sendmail => $CUSTOM{db_mail_path}, 
                                 from => $from, 
                                 subject => $subject,
                                 to => $to,
                                 msg => $msg                  
                            } ) or die $CUSTOM::Mailer::error;
	    $mailer->send or die $CUSTOM::Mailer::error;
}
elsif ($postnotify eq 'Y') {
	if (($forumnotify eq 'Y') and ($forummoderator eq 'N') and ($replierid ne '103')) {
		# Send Email to User
		# Check to make sure that there is an admin email address defined.
	    	$CUSTOM{db_forum_email} or die ("Admin Email Address Not Defined in config file!");
	    	$to      = $useremail;
	    	$from    = $CUSTOM{db_forum_email};
	    	$subject = "Post added to $FORUM{build_site_title}\n";
	    	$msg     = qq|
Dear $username,

You've added a reply to your trouble ticket.

You can view your post at:

$CUSTOM{build_forum_url}?showtopic=$postid

To view this post and other posts you've made in the 
Technical Support forum, you must use the following 
access information:

Username: $username
Password: $password

Regards,

Eliot Lee
Founder and Editor
Anthro TECH, L.L.C 
$FORUM{build_site_title}
$CUSTOM{build_forum_url}
$CUSTOM{db_forum_email}
|;

		# Then mail it away!    
	    		require Links::Mailer;
				$mailer = new Links::Mailer ( { 
				 smtp => $CUSTOM{db_smtp_server}, 
                                 sendmail => $CUSTOM{db_mail_path}, 
                                 from => $from, 
                                 subject => $subject,
                                 to => $to,
                                 msg => $msg                  
                            } ) or die $CUSTOM::Mailer::error;
	    		$mailer->send or die $CUSTOM::Mailer::error;
}
	else {
			# Send Email to User
			# Check to make sure that there is an admin email address defined.
			$CUSTOM{db_forum_email} or die ("Admin Email Address Not Defined in config file!");
	    		$to      = $useremail;
	    		$from    = $CUSTOM{db_forum_email};
	    		$subject = "Post added to $FORUM{build_site_title}\n";
	    		$msg     = qq|
Dear $username,

$postername has replied to your post in the $FORUM{build_site_title}:

$CUSTOM{build_forum_url}?showtopic=$postid

Regards,

Eliot Lee
Founder and Editor
Anthro TECH, L.L.C 
$FORUM{build_site_title}
$CUSTOM{build_forum_url}
$CUSTOM{db_forum_email}
|;     

		# Then mail it away!    
		    require Links::Mailer;
			$mailer = new Links::Mailer ( { 
				 smtp => $CUSTOM{db_smtp_server}, 
                                 sendmail => $CUSTOM{db_mail_path}, 
                                 from => $from, 
                                 subject => $subject,
                                 to => $to,
                                 msg => $msg                  
                            } ) or die $CUSTOM::Mailer::error;
	    		$mailer->send or die $CUSTOM::Mailer::error;
	}
}
	$cleanmess = &Links::DBSQL::clean_markup($postmess);
	$cleansub  = &Links::DBSQL::clean_markup($postsub);	
	&site_html_add_reply_success ({ForumID => $forumid, ForumName => $forumname, ParentPostID => $putpostid, PostID => $postid, PostSubject => $cleansub, PostMessage => $cleanmess, PostNotify => $postnotify, PostSig => $postsig, title_linked => $title_linked}, $dynamic);
	return;
}
