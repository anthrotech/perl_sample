#!/usr/local/bin/perl -w
# ==============================================================
# Favorite Posts
# Script Name: favpost.cgi
# Copyright 2001, Anthro TECH
# http://www.anthrotech.com/
# info@anthrotech.com
# 
# Store Favorite Posts
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
	my $FORUMFAVDB     = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Favorites.def";
        my $FORUMPOSTSDB   = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Posts.def";
        my $FORUMSDB       = new Links::DBSQL $CUSTOM{forum_def} . "Forum_Topics.def";     
        my $USERDB         = new Links::DBSQL $CUSTOM{members_def}  . "Users.def";
	use vars qw/%in %rec $rec $FORUMFAVDB $FORUMPOSTSDB $FORMSDB $USERDB $USER %USER/;
	$|++;	

	&main();
	
sub main {
# ---------------------------------------------------
# Create CGI object and figure out what to do.
#
	my $in      = new CGI;
	my $dynamic = $in->param('d') ? $in : undef;
	%in         = %{&cgi_to_hash ($in)};
	my ($found);

# Check the referer.
    if (@{$CUSTOM{db_referers}} and $ENV{'HTTP_REFERER'}) {
        $found = 0;
        foreach (@{$CUSTOM{db_referers}}) { $ENV{'HTTP_REFERER'} =~ /\Q$_\E/i and $found++ and last; }
        if (!$found) {
            my $title_linked = &build_linked_forum_title ("My Posts/Error: Unable to Process Form");
            &site_html_error ( { error => "Auto submission is not allowed in this directory. Please visit the site to add your entry."}, $in, $dynamic);
            return;
        }
    }

# Get user information.
	my $s = $in->param('s') || $in->cookie('s');
	$USER = &authenticate ($s);
	if (! defined $USER) {
		my $encurl = &Links::DBSQL::encode ("$CUSTOM{build_favposts_url}?$ENV{'QUERY_STRING'}");
		print $in->redirect("$CUSTOM{build_login_url}?to=$encurl") and return;            
	}
	if ($in->param('add')) {
	     print $in->header();
             &add ($in, $dynamic);
	}
	elsif ($in->param('delete')) {
	     print $in->header();
             &delete ($in, $dynamic);
	}
	elsif ($in->param('delete_all'))  { 
	     print $in->header();
	     &delete_all ($in, $dynamic); 
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
	my ($id, $postid, $posts, $printpost, $span, $rec);
	my $userid = $USER->{UserID};

# Get the user's links
	my $recs = $FORUMFAVDB->query ({UserID => "$USER->{'UserID'}", mh => $CUSTOM{modify_span}, page => ($in->param('page') || '1'), nh => ($in->param('nh') || '1'), ww => 1});

# Change the links into HTML.
	if ($FORUMFAVDB->hits) {
		foreach my $rec (@$recs) {
			$rec = $FORUMFAVDB->array_to_hash ($rec);
			$postid = $rec->{PostID};
			my $getlink = $FORUMPOSTSDB->get_record ($postid, 'HASH'); 
			     foreach (keys %$getlink) { 
				     $rec->{$_} = $getlink->{$_};
		             }
			$posts .= &site_html_favposts_link ($rec, $dynamic);
            }
# Span pages if more than 10 hits.
	($FORUMFAVDB->hits > $CUSTOM{modify_span}) and ($span = $FORUMFAVDB->toolbar());

# Display the page.
        my $title_linked = &build_linked_forum_title ("My Favorite Posts");
	&site_html_favposts ({UserID => $userid, Posts => $posts, span => $span, title_linked => $title_linked}, $dynamic);
	}

# No Post --> Display Error Page
      elsif (!$FORUMFAVDB->hits < 1) {
           my $title_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
           &site_html_error ({error => "You do not have any Bookmarked Posts stored in our database at this time.", title_linked => $title_linked}, $dynamic); 
      }

# If there is only ONE Post --> Display single link form
      else {
           foreach my $rec (@$recs) {
			$rec 	= $FORUMFAVDB->array_to_hash ($rec);	
			$postid = $rec->{PostID};
			my $posts = $FORUMPOSTSDB->get_record ($postid, 'HASH');
			$printpost .= &site_html_favposts_link ({%$posts});
      }
# Display the page.
        my $title_linked = &build_linked_forum_title ("My Favorite Posts");
	&site_html_favposts ({Posts => $printpost, %$USER, title_linked => $title_linked}, $dynamic);
      }
}

sub add {
# --------------------------------------------------------          
      my ($in, $dynamic) = @_;
      my ($error, $id, $posts, $rec); 
      my $postid = $in->param('add');
      my $userid = $USER->{UserID};
      my $title_linked = &build_linked_forum_title ("My Favorite Posts/Post Added");
      my $title_error_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
          
if ($postid =~ /^\d+$/) {
    
# Check that the record hasn't been added already in the Posts and Validate tables.
      $FORUMFAVDB->query ({PostID => $postid, ww => 1 }); 

      if ($FORUMFAVDB->hits) {
	  my $title_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
          &site_html_error ( { error => "You have already bookmarked this site.", title_linked => $title_linked}, $dynamic);
          return;
      }
      my $checkpost = $FORUMPOSTSDB->get_record ($postid, 'HASH');
      my $title_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
      ($checkpost) or &site_html_error ({error => "This favorite post does not exist. Please select another post in our Discussion Forum.", title_linked=> $title_linked}, $dynamic) and exit;
    
# Set date variable to today's date.
      $in->param ( -name => 'UserID', -value => $userid );
      $in->param ( -name => 'PostID', -value => $postid );
	
# Validate the form input.. 
      $rec  = &cgi_to_hash ( $in );
      if ($checkpost) {
	   $id  = $FORUMFAVDB->add_record ( $rec, $in );
      }

# Check ID before adding the record
      if ($id) {
          my $link = $FORUMPOSTSDB->get_record ($rec->{'PostID'}, 'HASH');
          my $title_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
	  ($link) or &site_html_error ({error => "Unable to get Post Information.", title_linked => $title_linked}, $dynamic) and exit;
	  my $postsub     = $link->{PostSubject};
	  my $add_post    = $link->{Add_Post};
          &site_html_favposts_add_success ({PostSubject => $postsub, Add_Post => $add_post, PostID => $postid, title_linked => $title_linked}, $dynamic) and exit;
      }
      else {
          &site_html_error ({error => "Post Unknown, Cannot add into your bookmarks.", title_linked => $title_error_linked}, $dynamic);      
      }
}
else {
      &site_html_error ({error => "Post not specified.", title_linked => $title_error_linked}, $dynamic);
}
}

sub delete {
# --------------------------------------------------------          
	my ($in, $dynamic) = @_;
	my $postid  = $in->param('delete');
	my $title_linked = &build_linked_forum_title ("My Favorite Posts/Bookmark Deleted");
	my $title_error_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");	
	
  if ($postid =~ /^\d+$/) {
	
# Connect to Favorite Posts Table
	my $rec = $FORUMFAVDB->get_prime_record ($postid, 'HASH');
	my $title_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
	($rec) or &site_html_error ({error => "Favorite Post not found or already deleted.", title_linked => $title_linked}, $in, $dynamic),return;
	$rec = $FORUMFAVDB->prepare ("SELECT 1 
				       FROM Forum_Favorites 
				       WHERE PostID = $postid");
	$rec->execute() or die $DBI::errstr; 

# Delete Post from Posts Table
	$FORUMFAVDB->do (qq! DELETE FROM Forum_Favorites WHERE PostID = $postid!);
	&site_html_favposts_delete_success ({title_linked => $title_linked}, $in, $dynamic);	
   }
   else {
        &site_html_error ({error => "Post not specified.", title_linked => $title_error_linked}, $dynamic);
   }   
}

sub delete_all {
# --------------------------------------------------------          
	my ($in, $dynamic) = @_;
	my $userid = $in->param('delete_all');

# Connect to Favorite Posts Table

	my $recs = $FORUMFAVDB->query ({UserID => $userid, ww => 1});

	if ($FORUMFAVDB->hits > 0) {	
		foreach my $rec (@$recs) {
# Delete from Favorite Posts table	
			$rec = $FORUMFAVDB->prepare ("DELETE 
				       FROM Forum_Favorites
				       WHERE UserID = '$userid'
        		");		
  	        	$rec->execute() or die $DBI::errstr; 
  	        }
		my $title_linked = &build_linked_forum_title ("My Favorite Posts/All Favorite Posts Deleted");
		&site_html_favposts_delete_all_success ({title_linked => $title_linked}, $in, $dynamic);	        
  	}
  	else {	
  		my $title_error_linked = &build_linked_forum_title ("My Favorite Posts/Error: Unable to Process Form");
		&site_html_error({error => "No Favorite Posts Found in our database.", title_linked => $title_error_linked}, $in, $dynamic);		
  	}
}