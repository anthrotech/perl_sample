#!/usr/local/bin/perl
####################################################################
# Send Post
# Script Name: sendpost.cgi
# Copyright 2001, Anthro TECH
# http://www.anthrotech.com/
# info@anthrotech.com
# 
# Sends Post Information to user with email address
####################################################################

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
#-------------------------------------------------------------------
# Main Routine

      my $in      = new CGI;
      my $dynamic = $in->param('d') ? $in : undef;
      my %in = %{&cgi_to_hash ($in)};
      my $id = $in->param('ID');
      my $title_linked = &build_linked_forum_title ("Send Post");
      my $title_error_linked = &build_linked_forum_title ("Send Post/Error: Unable to Process Form");
                 
      print $in->header();
      if ($in->param('process_form'))  { 
           &process_form ($in, $dynamic); 
      }          
      elsif ($id =~ /^\d+$/) {
	      my $rec = $FORUMPOSTSDB->get_record ($id, 'HASH');
		if ($rec) {
                 &site_html_sendpost_form ({title_linked => $title_linked, %in, %$rec}, $dynamic);
                 return;
		}
            else {
                 if ($CUSTOM{email_error}) {
                 		&send_error ({error => "Unknown Post ID: $id"}, $in);
                 }
                 &site_html_error ({ error => "Unknown Post ID: $id", title_linked => $title_linked}, $dynamic);
                 return;
            }
       }
       else {
            &site_html_error ({ error => "Post not defined. Please go back to our directory and select a link to send.", title_linked => $title_error_linked}, $dynamic);
            return;
       }
}

sub process_form {
#-------------------------------------------------------------------------
# Process Form

    my ($in, $dynamic) = @_;
    my ($error, $found, $title_linked, $rec);
    my $sendname  = $in->param('sendname');
    my $sender    = $in->param('sender');
    my $recipient = $in->param('recipient');
    my $recipmail = $in->param('recipmail');
    my $note      = $in->param('note');
    my $copy      = $in->param('copy');
    my $id        = $in->param('ID');
    my $in        = &cgi_to_hash ($in);
    my $title_error_linked = &build_linked_forum_title ("Send Post/Error: Unable to Process Form");
    my $title_linked = &build_linked_forum_title ("Send Post/Post Successfully Sent");	

# Check the referer.
    if (@{$CUSTOM{db_referers}} and $ENV{'HTTP_REFERER'}) {
        $found = 0;
        foreach (@{$CUSTOM{db_referers}}) { $ENV{'HTTP_REFERER'} =~ /\Q$_\E/i and $found++ and last; }
        if (!$found) {
              $error .= "<li>Auto Submission of this Form is not allowed.</li><br>";
         }
    }

# Email Check

      if (!$sendname) {
		$error .= "<li>You must provide <span class=\"boldredtext\">your name</span>.</li><br>"; 
      }	
      if (!$sender) {
            	$error .= "<li>You must provide <span class=\"boldredtext\">your email address</span>.</li><br>";
      }
      if (!$recipient) {
            	$error .= "<li>You must provide a <span class=\"boldredtext\">recipient name</span>.</li><br>";
      }
      if (!$recipmail) {
            	$error .= "<li>You must provide a <span class=\"boldredtext\">recipient email address</span>.</li><br>";
      }
      if (!$note) {
            	$error .= "<li>You must provide a <span class=\"boldredtext\">message</span>.</li><br>";
      }
	if (($sender) and ($recipmail)) {
         if ($sender !~ /.+\@.+\..+/)  { 
            	$error .= "<li>The format of your <span class=\"boldredtext\">email address</span> is incorrect.</li><br>";
         }
         if ($recipmail !~ /.+\@.+\..+/) {
            	$error .= "<li>The format of the <span class=\"boldredtext\">recipient email address</span> is incorrect.</li><br>";
	   }
         if ($sender eq $recipmail) {
            	$error .= "<li>Sorry, you cannot send this post to yourself. Please select another <span class=\"boldredtext\">recipient email address</span>.</li><br>";
         }
	}

if ($error) {
    	chomp($error);
    	&site_html_sendpost_failure({error => $error, title_linked => $title_error_linked, %$in}, $dynamic);
    	return;
}
else {
	if ($copy) {
     	   &send_copy($in);
        }
        &send_email($in);
    	&site_html_sendpost_success({title_linked => $title_linked, %$in}, $dynamic);
    	return;        
}
}

sub send_email {
# --------------------------------------------------------
# Sends an email to the admin, letting him know that there is
# a new link waiting to be deleted. No error checking as we don't
# want users to see the informative &cgierr output. 

    # Check to make sure that there is an admin email address defined.
    $CUSTOM{db_admin_email} or &cgierr("Admin Email Address Not Defined in config file!");
    my ($in) = @_;
    my ($to, $from, $subject, $msg, $mailer);
    my %in = %{$in};

    $to = $in{'recipmail'};
    $from = $in{'sender'};
    $subject = "$CUSTOM{build_forum_title}: Suggested Forum Post from $in{'sendname'}";
    $msg = qq|Dear $in{'recipient'},

$in{'sendname'} has recommended you view the following 
Forum Post:
----------------------------------------------------
    Title:  $in{'PostSubject'}

* To view this post, visit the following web page:

$CUSTOM{build_forum_url}?showtopic=$in{'PostID'}

----------------------------------------------------
Here is their attached message:
----------------------------------------------------

$in{'note'}

----------------------------------------------------
Remote Host: $ENV{'REMOTE_HOST'}
Remote Address: $ENV{'REMOTE_ADDR'}
Referer: $ENV{'HTTP_REFERER'}
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
                            } ) or die $Links::Mailer::error;
	    $mailer->send or die $Links::Mailer::error;

}

sub send_copy {
#------------------------------------------------------
# Sends email message to Administrator

# Check to make sure that there is an admin email address defined.
	    $CUSTOM{db_admin_email} or die ("Admin Email Address Not Defined in config file!");
    	    my ($in) = @_;
          my ($to, $from, $subject, $msg, $mailer);
          my %in = %{$in};

	    $to      = $in{'sender'};
	    $from    = $CUSTOM{db_admin_email};
	    $subject = "$CUSTOM{build_forum_title}: Suggested Forum Post: Copy of your message\n";
	    $msg     = qq|Here is the copy of the message you sent to $in{'recipient'}:

$in{'sendname'} has recommended you view the following 
Forum Post:
----------------------------------------------------
    Title:  $in{'PostSubject'}

* To view this post, visit the following web page:

$CUSTOM{build_forum_url}?showtopic=$in{'PostID'}

----------------------------------------------------
Here is their attached message:
----------------------------------------------------

$in{'note'}

----------------------------------------------------

Eliot Lee
$CUSTOM{build_site_title}
http://vlib.anthrotech.com/
$CUSTOM{db_admin_email}
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
                            } ) or die $Links::Mailer::error;
	    $mailer->send or die $Links::Mailer::error;
}