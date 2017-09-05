#!/usr/bin/perl
use File::Spec;
use strict;
use Digest::MD5 qw/md5_hex/;
use File::MimeInfo qw(globs);
use File::Basename 'basename', 'dirname';
use CGI;
use CGI::Cookie;

require DBD::SQLite;
require DBI;

require File::Spec->catfile(dirname(__FILE__),"../login/common.pl");
require File::Spec->catfile(dirname(__FILE__),"common_ndl.pl");

my $dbh = GetDatabaseHandleNicodl();
my $q = new CGI;

my $dbhId=GetDatabaseHandle();
my $hash= $q->cookie("login_session");
my $sessionHash= GetSessionData($dbhId,$hash);
#if(! $sessionHash){print $q->redirect('../login/');exit;}

print "Content-Type: application/json;charset=utf-8;\n\n";

my $sth;
if($sessionHash){
  $sth=$dbh->prepare("select * from collection where owner = ".$sessionHash->{"id"}." or public = 1");
}else{
  $sth=$dbh->prepare("select * from collection where public = 1");
}
$sth->execute;

print "[\n";
my $first1=1;
while(my $hash=$sth->fetchrow_hashref()){
   if($first1!=1){print ",\n";}
  $first1=0;
  print "  {\n";
  print "    \"title\":\"".EscapeJson($hash->{"title"})."\",\n";
  print "    \"url\":\"".EscapeJson($hash->{"url"})."\",\n";
  print "    \"public\":\"".EscapeJson($hash->{"public"})."\",\n";
  print "    \"videos\":[\n";
  my $sth2=$dbh->prepare("select * from movie where group_id = ".$hash->{"id"}." order by watch_id");
  $sth2->execute;
  my $first2=1;
  while(my $hash2=$sth2->fetchrow_hashref()){
    if($first2!=1){print ",\n";}
    $first2=0;
    print "      {\n";
    print "        \"title\":\"".EscapeJson($hash2->{"title"})."\",\n";
    print "        \"wath_id\":\"".EscapeJson($hash2->{"watch_id"})."\",\n";
    print "        \"public\":\"".EscapeJson($hash2->{"public"})."\",\n";
    print "        \"play\":\"play.html\#".EscapeJson($hash2->{"watch_id"})."\",\n";
    print "        \"path\":\"movie.cgi/".EscapeJson($hash2->{"watch_id"})."\"\n";
    print "      }";
  }
  print "\n    ]\n";
  print "  }";
}
print "\n]\n"
