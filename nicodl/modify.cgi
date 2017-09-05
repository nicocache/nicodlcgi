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
my $op=$q->param('op');

my $dbhId=GetDatabaseHandle();
my $hash= $q->cookie("login_session");
my $sessionHash= GetSessionData($dbhId,$hash);
if(! $sessionHash){print $q->redirect('../login/');exit;}

if($op eq "add"){
  my $url=$q->param('url');
  my ($type,$content)=GetUrlInfo($url);

  print $q->header;
  print $q->start_html(-title=>'command');
  if($type eq "failed"){
    print "<p>Wrong url</p>";
  }else{
    $dbh->do("insert into download(id,owner,public,kind,url,keep_watching) select case when max(id) is null then 1 else max(id) +1 end,".$sessionHash->{"id"}.",".($q->param('public') eq "true"?1:0).",'".escape_sql($type)."','".escape_sql($content)."',".($q->param('keep') eq "true"?1:0)." from download;") or print "Sql failed";
    print "<p>Succeeded</p>\n";
  }
  print $q->end_html;
  exit;
}else{
  print $q->header;
  print $q->start_html(-title=>'command');
  print "<p>Command not specified</p>";
  print "<p>You are ".$sessionHash->{"login"}."</p>";
  print $q->end_html;
  exit;
}
