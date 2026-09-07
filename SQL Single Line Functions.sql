-- 1) upper
-- select upper('data') from dual

-- select first_name ,upper(first_name) from hr.employees

-- 2) lower
-- select lower('DATA') from dual

-- select first_name, lower(first_name) from hr.employees

-- 3) initcap
-- select initcap('data science') from dual

-- select initcap(first_name) from hr.employees

-- 4) length
-- select length('yuvaraj') from dual

-- select length(first_name) from hr.employees

-- 4) substr
-- select substr('yuvaraj',1,4) from dual

-- select substr('yuvaraj',-3) from dual

-- select substr(first_name,1,3) from hr.employees

-- select substr(first_name,-3) from hr.employees

-- 6) concat
-- select concat('data',' ','science') from dual

-- select concat(first_name,' ',last_name) from hr.employees

-- select first_name || ' ' || last_name as full_name from hr.employees

-- 7) replace
-- select replace('data science','science','engineering') from dual

-- select replace(first_name,'a','@') from hr.employees

-- 8)trim
-- select trim('   data   ') from dual

-- select * from hr.employees where trim(first_name) = 'Steven'

-- 9) ltrim
-- select ltrim('***data','*') from dual

-- select first_name, ltrim(first_name) from hr.employees

-- 10) rtrim
-- select rtrim('data*****','*') from dual

-- select first_name, rtrim(first_name) from hr.employees

-- 11) lpad
-- select lpad('123',6,'*') from dual

-- select lpad(employee_id,6,'0') from hr.employees

-- 12) rpad
-- select rpad('data',6,'$') from dual

-- select first_name, rpad(first_name,15,'.') from hr.employees

-- 13) ascii
-- select ascii('C') from dual

-- select first_name, ascii(first_name) from hr.employees

-- 14) chr
-- select chr(68) from dual

-- select employee_id, chr(employee_id) from hr.employees

-- 15) ceil
-- select ceil(10.1) from dual

-- select salary, salary/12, ceil(salary/12) from hr.employees

-- 16) floor
-- select floor(12.3) from dual

-- select salary, salary/12, floor(salary/12) from hr.employees

-- 17) mod
-- select mod(10,3) from dual

-- select employee_id ,first_name from hr.employees where mod(employee_id,2) = 1

-- 18) abs
-- select abs(-10.6) from dual

-- select employee_id,salary, abs(salary-10000) as salary_difference from hr.employees

-- 19) power
-- select power(2,3) from dual

-- select employee_id , salary , power(salary,2) from hr.employees

-- 20) sqrt
-- select sqrt(16) from dual

-- select employee_id, salary, sqrt(salary) from hr.employees



