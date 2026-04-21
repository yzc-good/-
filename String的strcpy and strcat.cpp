//string 中的两个函数strcpy and strcat;
这两个函数一般少见，因为再C++中直接用string的语法来写

#include<iostream>
#include<string>
using namespace std;

int main()
{
    char arr1[] = "hello world";
    char arr2[40];
    string arr3 = "hello world";
    string arr4;
    //实现char类型字符串的拷贝
    strcpy(arr2, arr1);//参数1：目标字符串，参数2：拷贝字符串
    arr4 = arr3;
    cout << arr2 << arr1<<endl;
    cout << arr4 << arr3<<endl;
    //实现再目标字符串后追加字符
    strcat(arr2, arr1);//参数1：目标字符串，参数2：追加字符串
    arr4 += arr3;
    cout << arr2 << arr1 << endl;
    cout << arr4 << arr3 << endl;
    return 0;
}
