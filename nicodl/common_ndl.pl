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

sub GetDatabaseHandleNicodl{
  my %conf=GetConf(File::Spec->catfile(dirname(__FILE__),"dl.conf"));
  my $dbh = DBI->connect("dbi:SQLite:dbname=".$conf{"sqlitedb"});
  $dbh->{sqlite_unicode} = 1;
  $dbh->do("create table if not exists download(id,owner,public,kind,url,keep_watching);");
  $dbh->do("create table if not exists movie(id,owner,public,title,path,group_id,watch_id);");
  $dbh->do("create table if not exists collection(id,owner,public,title,url);");
  return $dbh;
}

sub GetUrlInfo{
  my ($url)=@_;
  if($url=~ m!/watch/([a-zA-Z0-9]+)!){return ("video",$1);}
  if($url=~ m!/mylist/(\d+)!){return ("mylist",$1);}
  if($url=~ m![a-zA-Z0-9]{0,2}\d+!){return ("video",$1);}
  return ("failed",$url);
}

sub escape_sql{
  my $str=$_[0];
  if(defined($str)){
    $str=~ s/\\/\\\\\\\\/go;
    $str=~ s/'/''/go;
    $str=~ s/%/\\\\%/go;
    $str=~ s/_/\\\\_/go;
  }
  return $str;
}

sub EscapeJson{
  my $text=$_[0];
  $text=~ s/([\\\"])/\\$1/g;
  return $text;
}

1;
