use treeohealthdb;
select * from users_acc_user;
UPDATE users_acc_user SET is_email_confirmed=1 WHERE username = "first_user";
