<<//左移
>>//右移
&//按位与   &1最常见
|//按位或
^//按位异或
~//取反
  
//在这个样例中，对i这个数最后一位或者是任意一位判断思维可以用在其他题目中
#include<bits/stdc++.h>
 using namespace std;
 
 int main()
 {
 	int n;
 	cin>>n;
 	int total=1<<n;//2^n,安全写法,1左移一位就是2^1，两位就是2^2,n位就是2^n 
	for(int i=0;i<total;i++)
	{
		for(int j=n-1;j>=0;j--)//从高位向低位输出
		{
			if(i&(1<<j))//i&1是判断i二进制的最后一位是否是1,将1左移j位，就可以判断i的第j位是否是1 
			{
				cout<<'Y';
			}
			else
			{
				cout<<'N';
			}
		}
		cout<<"\n";
	 } 
 	return 0;
  } 
